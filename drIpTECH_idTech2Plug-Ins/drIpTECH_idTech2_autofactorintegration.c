
#include "include/drIpTECH_idTech2_autofactorintegration.h"

#include <stdio.h>

static const char *safe_string(const char *value) {
	return value ? value : "";
}

static void write_c_string(FILE *f, const char *value) {
	const char *cursor = safe_string(value);
	fputc('"', f);
	for (; *cursor; ++cursor) {
		if (*cursor == '"' || *cursor == '\\') {
			fputc('\\', f);
		}
		fputc(*cursor, f);
	}
	fputc('"', f);
}

static int write_header(FILE *hf, const char *prefix) {
	fprintf(hf, "#ifndef DRIPTECH_GENERATED_REGISTRY_H\n#define DRIPTECH_GENERATED_REGISTRY_H\n\n");
	fprintf(hf, "typedef struct DriptechGeneratedAsset { const char *id; const char *path; const char *type; } DriptechGeneratedAsset;\n");
	fprintf(hf, "typedef struct DriptechGeneratedPrecache { const char *alias; const char *path; const char *type; } DriptechGeneratedPrecache;\n");
	fprintf(hf, "typedef struct DriptechGeneratedDispatch { const char *system_name; const char *init_fn; const char *tick_fn; } DriptechGeneratedDispatch;\n");
	fprintf(hf, "typedef struct DriptechGeneratedSpawn { const char *id; const char *classname; const char *asset_id; int x; int y; int z; } DriptechGeneratedSpawn;\n\n");
	fprintf(hf, "extern const DriptechGeneratedAsset %s_assets[];\n", prefix);
	fprintf(hf, "extern const int %s_asset_count;\n", prefix);
	fprintf(hf, "extern const DriptechGeneratedPrecache %s_precache[];\n", prefix);
	fprintf(hf, "extern const int %s_precache_count;\n", prefix);
	fprintf(hf, "extern const char *%s_systems[];\n", prefix);
	fprintf(hf, "extern const int %s_system_count;\n", prefix);
	fprintf(hf, "extern const DriptechGeneratedDispatch %s_dispatch[];\n", prefix);
	fprintf(hf, "extern const int %s_dispatch_count;\n", prefix);
	fprintf(hf, "extern const DriptechGeneratedSpawn %s_spawns[];\n", prefix);
	fprintf(hf, "extern const int %s_spawn_count;\n\n", prefix);
	fprintf(hf, "#endif\n");
	return 1;
}

int driptech_idtech2_emit_runtime(
	const char *header_path,
	const char *source_path,
	const char *prefix,
	const DriptechIdAsset *assets,
	size_t asset_count,
	const DriptechIdPrecache *precache,
	size_t precache_count,
	const DriptechIdSystem *systems,
	size_t system_count,
	const DriptechIdDispatch *dispatch,
	size_t dispatch_count,
	const DriptechIdSpawn *spawns,
	size_t spawn_count) {
	FILE *hf;
	FILE *sf;
	size_t i;

	if (!header_path || !source_path || !prefix) return 0;

	hf = fopen(header_path, "wb");
	if (!hf) return 0;
	sf = fopen(source_path, "wb");
	if (!sf) {
		fclose(hf);
		return 0;
	}

	write_header(hf, prefix);
	fprintf(sf, "#include \"driptech_generated_registry.h\"\n\n");

	fprintf(sf, "const DriptechGeneratedAsset %s_assets[] = {\n", prefix);
	for (i = 0; assets && i < asset_count; ++i) {
		fprintf(sf, "    { ");
		write_c_string(sf, assets[i].asset_id);
		fprintf(sf, ", ");
		write_c_string(sf, assets[i].asset_path);
		fprintf(sf, ", ");
		write_c_string(sf, assets[i].asset_type);
		fprintf(sf, " },\n");
	}
	fprintf(sf, "};\nconst int %s_asset_count = %u;\n\n", prefix, (unsigned)asset_count);

	fprintf(sf, "const DriptechGeneratedPrecache %s_precache[] = {\n", prefix);
	for (i = 0; precache && i < precache_count; ++i) {
		fprintf(sf, "    { ");
		write_c_string(sf, precache[i].alias);
		fprintf(sf, ", ");
		write_c_string(sf, precache[i].asset_path);
		fprintf(sf, ", ");
		write_c_string(sf, precache[i].asset_type);
		fprintf(sf, " },\n");
	}
	fprintf(sf, "};\nconst int %s_precache_count = %u;\n\n", prefix, (unsigned)precache_count);

	fprintf(sf, "const char *%s_systems[] = {\n", prefix);
	for (i = 0; systems && i < system_count; ++i) {
		fprintf(sf, "    ");
		write_c_string(sf, systems[i].system_name);
		fprintf(sf, ",\n");
	}
	fprintf(sf, "};\nconst int %s_system_count = %u;\n\n", prefix, (unsigned)system_count);

	fprintf(sf, "const DriptechGeneratedDispatch %s_dispatch[] = {\n", prefix);
	for (i = 0; dispatch && i < dispatch_count; ++i) {
		fprintf(sf, "    { ");
		write_c_string(sf, dispatch[i].system_name);
		fprintf(sf, ", ");
		write_c_string(sf, dispatch[i].init_fn);
		fprintf(sf, ", ");
		write_c_string(sf, dispatch[i].tick_fn);
		fprintf(sf, " },\n");
	}
	fprintf(sf, "};\nconst int %s_dispatch_count = %u;\n\n", prefix, (unsigned)dispatch_count);

	fprintf(sf, "const DriptechGeneratedSpawn %s_spawns[] = {\n", prefix);
	for (i = 0; spawns && i < spawn_count; ++i) {
		fprintf(sf, "    { ");
		write_c_string(sf, spawns[i].entity_id);
		fprintf(sf, ", ");
		write_c_string(sf, spawns[i].classname);
		fprintf(sf, ", ");
		write_c_string(sf, spawns[i].asset_id);
		fprintf(sf, ", %d, %d, %d },\n", spawns[i].x, spawns[i].y, spawns[i].z);
	}
	fprintf(sf, "};\nconst int %s_spawn_count = %u;\n", prefix, (unsigned)spawn_count);

	fclose(hf);
	fclose(sf);
	return 1;
}

int driptech_idtech2_emit_registry(
	const char *header_path,
	const char *source_path,
	const char *prefix,
	const DriptechIdAsset *assets,
	size_t asset_count,
	const DriptechIdSystem *systems,
	size_t system_count,
	const DriptechIdSpawn *spawns,
	size_t spawn_count) {
	return driptech_idtech2_emit_runtime(
		header_path,
		source_path,
		prefix,
		assets,
		asset_count,
		NULL,
		0,
		systems,
		system_count,
		NULL,
		0,
		spawns,
		spawn_count);
}
