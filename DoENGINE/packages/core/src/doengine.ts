// doengine.ts
// Core engine entry for DoENGINE: frequency-based, motion/vibration-driven

import { encryptTrace } from '../../encryption/src/encryptor';
import { DoTraceRecord, HardwareSignatureProvider, SessionKeyProvider } from '../../shared/src/contracts';
import { writeTrace } from '../../telemetry/src/trace-writer';

export class Doer {
    constructor(
        public id: string,
        public motif: string,
        public vibe: string,
        private readonly hardwareSignatureProvider: HardwareSignatureProvider = getHardwareSignature,
        private readonly sessionKeyProvider: SessionKeyProvider = getSessionKey,
    ) {}

    act(action: string) {
        const trace: DoTraceRecord = {
            timestamp: new Date().toISOString(),
            doer: this.id,
            motif: this.motif,
            vibe: this.vibe,
            action,
            hardware: this.hardwareSignatureProvider(),
        };
        const encrypted = encryptTrace(trace, trace.hardware, this.sessionKeyProvider());
        writeTrace(encrypted);
    }
}

function getHardwareSignature(): string {
    // Placeholder: generate unique hardware signature
    return 'HWID-' + Math.random().toString(36).slice(2, 10);
}

function getSessionKey(): string {
    // Placeholder: generate session key
    return 'SESSION-' + Math.random().toString(36).slice(2, 10);
}

export class DoENGINE {
    doers: Doer[] = [];
    pulse: number = 0;
    frequency: number = 60; // Hz
    running: boolean = false;

    start() {
        this.running = true;
        this.pulse = 0;
        this.loop();
    }

    loop() {
        if (!this.running) return;
        this.pulse++;
        this.doers.forEach(doer => doer.act('pulse'));
        setTimeout(() => this.loop(), 1000 / this.frequency);
    }

    addDoer(doer: Doer) {
        this.doers.push(doer);
    }

    stop() {
        this.running = false;
    }
}
