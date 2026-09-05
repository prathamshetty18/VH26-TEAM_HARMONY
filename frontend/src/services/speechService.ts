import type { VoiceTranscriptionResult } from '../types';

export class SpeechService {
  private activeRecognition: any = null;
  private audioContext: AudioContext | null = null;
  private mediaStream: MediaStream | null = null;
  private scriptNode: ScriptProcessorNode | null = null;
  private analyser: AnalyserNode | null = null;
  private pcmChunks: Float32Array[] = [];
  private silenceTimer: any = null;
  private speechDetected: boolean = false;

  /**
   * Starts listening to user microphone audio and converts it to text in real-time
   * using Web Speech API (Google Speech-to-Text engine) or AudioContext WAV capture.
   */
  public listenSpeech(options: {
    onStart?: () => void;
    onResult: (transcript: string) => void;
    onError: (errorMessage: string) => void;
    onEnd: () => void;
    baseUrl?: string;
  }): { stop: () => void } {
    const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;

    if (SpeechRecognition) {
      try {
        const recognition = new SpeechRecognition();
        this.activeRecognition = recognition;
        recognition.continuous = false;
        recognition.interimResults = false;
        recognition.maxAlternatives = 1;
        recognition.lang = 'en-US';

        let hasResult = false;
        let hasError = false;

        recognition.onstart = () => {
          options.onStart?.();
        };

        recognition.onresult = (event: any) => {
          if (event.results && event.results.length > 0 && event.results[0].length > 0) {
            const rawText = event.results[0][0].transcript.trim();
            if (rawText) {
              hasResult = true;
              options.onResult(rawText);
            }
          }
        };

        recognition.onerror = (event: any) => {
          hasError = true;
          if (event.error === 'not-allowed' || event.error === 'service-not-allowed') {
            options.onError('Microphone permission is required for voice input.');
          } else if (event.error === 'no-speech') {
            options.onError('No speech detected. Please try again.');
          } else {
            options.onError('Unable to transcribe audio. Please try again.');
          }
        };

        recognition.onspeechend = () => {
          try { recognition.stop(); } catch {}
        };

        recognition.onend = () => {
          this.activeRecognition = null;
          options.onEnd();
          if (!hasResult && !hasError) {
            options.onError('No speech detected. Please try again.');
          }
        };

        recognition.start();

        return {
          stop: () => {
            try {
              if (this.activeRecognition) {
                this.activeRecognition.stop();
                this.activeRecognition = null;
              } else {
                recognition.stop();
              }
            } catch {}
          }
        };
      } catch (err) {
        console.warn('SpeechRecognition failed to start, falling back to AudioContext:', err);
      }
    }

    // Fallback: AudioContext WAV Recorder with silence detection
    this.startWavListening(options);
    return {
      stop: () => {
        this.stopWavListeningAndTranscribe(options);
      }
    };
  }

  private async startWavListening(options: {
    onStart?: () => void;
    onResult: (transcript: string) => void;
    onError: (errorMessage: string) => void;
    onEnd: () => void;
    baseUrl?: string;
  }): Promise<void> {
    try {
      if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        options.onError('Microphone permission is required for voice input.');
        options.onEnd();
        return;
      }

      this.mediaStream = await navigator.mediaDevices.getUserMedia({
        audio: { echoCancellation: true, noiseSuppression: true, autoGainControl: true }
      });

      const AudioContextClass = window.AudioContext || (window as any).webkitAudioContext;
      this.audioContext = new AudioContextClass({ sampleRate: 16000 });
      const source = this.audioContext.createMediaStreamSource(this.mediaStream);

      this.analyser = this.audioContext.createAnalyser();
      this.analyser.fftSize = 512;
      source.connect(this.analyser);

      this.scriptNode = this.audioContext.createScriptProcessor(4096, 1, 1);
      this.pcmChunks = [];
      this.speechDetected = false;

      const dataArray = new Uint8Array(this.analyser.frequencyBinCount);

      this.scriptNode.onaudioprocess = (e) => {
        const channelData = e.inputBuffer.getChannelData(0);
        this.pcmChunks.push(new Float32Array(channelData));

        if (this.analyser) {
          this.analyser.getByteFrequencyData(dataArray);
          let sum = 0;
          for (let i = 0; i < dataArray.length; i++) sum += dataArray[i];
          const avg = sum / dataArray.length;

          if (avg > 15) {
            this.speechDetected = true;
            if (this.silenceTimer) {
              clearTimeout(this.silenceTimer);
              this.silenceTimer = null;
            }
          } else if (this.speechDetected && !this.silenceTimer) {
            this.silenceTimer = setTimeout(() => {
              this.stopWavListeningAndTranscribe(options);
            }, 1600);
          }
        }
      };

      source.connect(this.scriptNode);
      this.scriptNode.connect(this.audioContext.destination);

      options.onStart?.();
    } catch (err: any) {
      this.cleanupAudio();
      options.onEnd();
      if (err.name === 'NotAllowedError' || err.name === 'PermissionDeniedError') {
        options.onError('Microphone permission is required for voice input.');
      } else {
        options.onError('Unable to transcribe audio. Please try again.');
      }
    }
  }

  private stopWavListeningAndTranscribe(options: {
    onResult: (transcript: string) => void;
    onError: (errorMessage: string) => void;
    onEnd: () => void;
    baseUrl?: string;
  }): void {
    let totalLength = 0;
    for (const chunk of this.pcmChunks) totalLength += chunk.length;

    if (totalLength < 4000 || !this.speechDetected) {
      this.cleanupAudio();
      options.onEnd();
      options.onError('No speech detected. Please try again.');
      return;
    }

    const merged = new Float32Array(totalLength);
    let offset = 0;
    for (const chunk of this.pcmChunks) {
      merged.set(chunk, offset);
      offset += chunk.length;
    }

    const wavBlob = this.encodeWAV(merged, 16000);
    this.cleanupAudio();

    const baseUrl = options.baseUrl || 'http://localhost:8000';
    this.transcribeAudio(wavBlob, baseUrl)
      .then((res) => {
        if (res && res.transcription && res.transcription.trim()) {
          options.onResult(res.transcription.trim());
        } else {
          options.onError('No speech detected. Please try again.');
        }
      })
      .catch((err) => {
        const msg = err.message && err.message.includes('No speech')
          ? 'No speech detected. Please try again.'
          : 'Unable to transcribe audio. Please try again.';
        options.onError(msg);
      })
      .finally(() => {
        options.onEnd();
      });
  }

  public async transcribeAudio(
    audioBlob: Blob,
    baseUrl: string = 'http://localhost:8000',
    languageHint?: string
  ): Promise<VoiceTranscriptionResult> {
    const base64Data = await this.blobToBase64(audioBlob);

    try {
      const endpoint = `${baseUrl}/api/voice/transcribe`;
      const response = await fetch(endpoint, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json',
        },
        body: JSON.stringify({
          audio: base64Data,
          format: audioBlob.type || 'audio/wav',
          language: languageHint || undefined,
        }),
        signal: AbortSignal.timeout(12000),
      });

      if (response.ok) {
        const data = await response.json();
        if (data.status === 'error') {
          throw new Error(data.error || 'Unable to transcribe audio. Please try again.');
        }
        return {
          transcription: data.transcription,
          detectedLanguage: data.detectedLanguage,
          languageName: data.languageName,
          englishText: data.englishText,
          isTranslated: data.isTranslated,
          confidence: data.confidence,
        };
      } else {
        const errJson = await response.json().catch(() => ({}));
        throw new Error(errJson.detail || 'Unable to transcribe audio. Please try again.');
      }
    } catch (err: any) {
      throw new Error(err.message || 'Unable to transcribe audio. Please try again.');
    }
  }

  private cleanupAudio(): void {
    if (this.silenceTimer) {
      clearTimeout(this.silenceTimer);
      this.silenceTimer = null;
    }
    if (this.scriptNode) {
      try { this.scriptNode.disconnect(); } catch {}
      this.scriptNode = null;
    }
    if (this.analyser) {
      try { this.analyser.disconnect(); } catch {}
      this.analyser = null;
    }
    if (this.mediaStream) {
      try { this.mediaStream.getTracks().forEach((t) => t.stop()); } catch {}
      this.mediaStream = null;
    }
    if (this.audioContext && this.audioContext.state !== 'closed') {
      try { this.audioContext.close(); } catch {}
      this.audioContext = null;
    }
    this.pcmChunks = [];
    this.speechDetected = false;
  }

  private encodeWAV(samples: Float32Array, sampleRate: number): Blob {
    const buffer = new ArrayBuffer(44 + samples.length * 2);
    const view = new DataView(buffer);

    const writeString = (v: DataView, off: number, str: string) => {
      for (let i = 0; i < str.length; i++) v.setUint8(off + i, str.charCodeAt(i));
    };

    writeString(view, 0, 'RIFF');
    view.setUint32(4, 36 + samples.length * 2, true);
    writeString(view, 8, 'WAVE');
    writeString(view, 12, 'fmt ');
    view.setUint32(16, 16, true);
    view.setUint16(20, 1, true); // PCM
    view.setUint16(22, 1, true); // Mono
    view.setUint32(24, sampleRate, true);
    view.setUint32(28, sampleRate * 2, true);
    view.setUint16(32, 2, true);
    view.setUint16(34, 16, true);
    writeString(view, 36, 'data');
    view.setUint32(40, samples.length * 2, true);

    let idx = 44;
    for (let i = 0; i < samples.length; i++) {
      const s = Math.max(-1, Math.min(1, samples[i]));
      view.setInt16(idx, s < 0 ? s * 0x8000 : s * 0x7FFF, true);
      idx += 2;
    }

    return new Blob([view], { type: 'audio/wav' });
  }

  private blobToBase64(blob: Blob): Promise<string> {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onloadend = () => {
        const res = reader.result as string;
        resolve(res);
      };
      reader.onerror = reject;
      reader.readAsDataURL(blob);
    });
  }
}

export const speechService = new SpeechService();
