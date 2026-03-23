// trace-writer.ts
// Writes encrypted traces into the normalized threefold backup structure.
import * as fs from 'fs';
import * as path from 'path';

function resolveBackupRoots(): string[] {
	const configuredRoot = process.env.DOENGINE_BACKUP_ROOT;
	if (configuredRoot) {
		return ['primary', 'secondary', 'tertiary'].map((tier) => path.resolve(configuredRoot, tier));
	}

	const backupRoot = path.resolve(__dirname, '../../../ops/backup');
	return ['primary', 'secondary', 'tertiary'].map((tier) => path.join(backupRoot, tier));
}

export function writeTrace(encryptedTrace: string) {
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
    const filename = `trace-${timestamp}.dat`;
    const paths = resolveBackupRoots();
    for (const root of paths) {
        fs.mkdirSync(root, { recursive: true });
        fs.writeFileSync(path.join(root, filename), encryptedTrace, 'utf8');
    }
}
