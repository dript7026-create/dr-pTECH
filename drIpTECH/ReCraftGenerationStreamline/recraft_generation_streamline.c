(void)0;
/*
 * ReCraft generation streamline (manifest-driven, JSON parsing via cJSON)
 *
 * Build requirements:
 *  - libcurl development files
 *  - cJSON (https://github.com/DaveGamble/cJSON) - include cJSON.h and link cjson.c
 * Example build:
 *   gcc recraft_generation_streamline.c cJSON.c -o recraft_gen -lcurl
 *
 * Usage:
 *  - Single call:
 *      ./recraft_gen "a small chibi sprite" 16 16 assets/tommy_sprite.png
 *  - Manifest (JSON array) call:
 *      ./recraft_gen --manifest manifest.json
 *
 * Manifest example (manifest.json):
 * [
 *   {"name":"tommy_sprite","prompt":"16x16 pixel chibi...","w":16,"h":16,"out":"assets/tommy_sprite.png"}
 * ]
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <curl/curl.h>
#include "cJSON.h"

struct membuf { char *buf; size_t len; };

static size_t write_cb(void *ptr, size_t size, size_t nmemb, void *userdata) {
	size_t realsize = size * nmemb;
	struct membuf *m = (struct membuf *)userdata;
	char *p = realloc(m->buf, m->len + realsize + 1);
	if (!p) return 0;
	m->buf = p;
	memcpy(&(m->buf[m->len]), ptr, realsize);
	m->len += realsize;
	m->buf[m->len] = '\0';
	return realsize;
}

/* base64 decode */
static const unsigned char b64_table[256] = {0};
/* simple base64 decoder using libc functions for clarity */
#include <ctype.h>
unsigned char *base64_decode(const char *data, size_t input_length, size_t *out_len);

/* forward declarations */
int http_post_json(const char *url, const char *api_key, const char *json_payload, struct membuf *resp);
int save_binary_file(const char *path, const unsigned char *data, size_t len);
char *read_file_to_string(const char *path);

/* Note: payload construction is handled in generate_and_save to allow
   runtime overrides (model, response_format) and to build size from w/h. */

int save_binary_file(const char *path, const unsigned char *data, size_t len) {
	FILE *f = fopen(path, "wb");
	if (!f) return 1;
	size_t w = fwrite(data, 1, len, f);
	fclose(f);
	return (w == len) ? 0 : 2;
}

char *read_file_to_string(const char *path) {
	FILE *f = fopen(path, "rb");
	if (!f) return NULL;
	fseek(f, 0, SEEK_END);
	long s = ftell(f);
	fseek(f, 0, SEEK_SET);
	char *buf = malloc(s + 1);
	if (!buf) { fclose(f); return NULL; }
	fread(buf, 1, s, f);
	buf[s] = '\0';
	fclose(f);
	return buf;
}

int http_post_json(const char *url, const char *api_key, const char *json_payload, struct membuf *resp) {
	CURL *curl = curl_easy_init();
	if (!curl) return 1;
	struct curl_slist *hdrs = NULL;
	char authbuf[1024];
	snprintf(authbuf, sizeof(authbuf), "Authorization: Bearer %s", api_key);
	hdrs = curl_slist_append(hdrs, authbuf);
	hdrs = curl_slist_append(hdrs, "Content-Type: application/json");
	curl_easy_setopt(curl, CURLOPT_URL, url);
	curl_easy_setopt(curl, CURLOPT_HTTPHEADER, hdrs);
	curl_easy_setopt(curl, CURLOPT_POSTFIELDS, json_payload);
	curl_easy_setopt(curl, CURLOPT_TIMEOUT, 120L);
	curl_easy_setopt(curl, CURLOPT_WRITEFUNCTION, write_cb);
	curl_easy_setopt(curl, CURLOPT_WRITEDATA, (void *)resp);
	CURLcode rc = curl_easy_perform(curl);
	long code = 0;
	curl_easy_getinfo(curl, CURLINFO_RESPONSE_CODE, &code);
	curl_slist_free_all(hdrs);
	curl_easy_cleanup(curl);
	if (rc != CURLE_OK) return 2;
	if (code >= 400) return (int)code;
	return 0;
}

int http_fetch_binary(const char *url, const char *api_key, struct membuf *resp) {
	CURL *curl = curl_easy_init();
	if (!curl) return 1;
	struct curl_slist *hdrs = NULL;
	if (api_key) {
		char authbuf[1024];
		snprintf(authbuf, sizeof(authbuf), "Authorization: Bearer %s", api_key);
		hdrs = curl_slist_append(hdrs, authbuf);
		curl_easy_setopt(curl, CURLOPT_HTTPHEADER, hdrs);
	}
	curl_easy_setopt(curl, CURLOPT_URL, url);
	curl_easy_setopt(curl, CURLOPT_WRITEFUNCTION, write_cb);
	curl_easy_setopt(curl, CURLOPT_WRITEDATA, (void *)resp);
	CURLcode rc = curl_easy_perform(curl);
	long code = 0; curl_easy_getinfo(curl, CURLINFO_RESPONSE_CODE, &code);
	curl_slist_free_all(hdrs);
	curl_easy_cleanup(curl);
	if (rc != CURLE_OK) return 2;
	if (code >= 400) return (int)code;
	return 0;
}

/* POST multipart/form-data using curl_mime; form_fields is a cJSON object of key->value, files is cJSON array of file paths (objects or strings) */
int http_post_multipart(const char *url, const char *api_key, cJSON *form_fields, cJSON *files, struct membuf *resp) {
	CURL *curl = curl_easy_init();
	if (!curl) return 1;
	struct curl_slist *hdrs = NULL;
	if (api_key) {
		char authbuf[1024];
		snprintf(authbuf, sizeof(authbuf), "Authorization: Bearer %s", api_key);
		hdrs = curl_slist_append(hdrs, authbuf);
	}
	curl_easy_setopt(curl, CURLOPT_URL, url);
	if (hdrs) curl_easy_setopt(curl, CURLOPT_HTTPHEADER, hdrs);
	curl_mime *mime = curl_mime_init(curl);
	if (!mime) { curl_slist_free_all(hdrs); curl_easy_cleanup(curl); return 2; }
	/* add form fields */
	if (form_fields && form_fields->child) {
		cJSON *f = form_fields->child;
		while (f) {
			if (cJSON_IsString(f)) {
				curl_mimepart *part = curl_mime_addpart(mime);
				curl_mime_name(part, f->string);
				curl_mime_data(part, f->valuestring, CURL_ZERO_TERMINATED);
			} else if (cJSON_IsNumber(f)) {
				char tmp[64]; snprintf(tmp, sizeof(tmp), "%g", f->valuedouble);
				curl_mimepart *part = curl_mime_addpart(mime);
				curl_mime_name(part, f->string);
				curl_mime_data(part, tmp, CURL_ZERO_TERMINATED);
			} else if (cJSON_IsBool(f)) {
				curl_mimepart *part = curl_mime_addpart(mime);
				curl_mime_name(part, f->string);
				curl_mime_data(part, cJSON_IsTrue(f) ? "true" : "false", CURL_ZERO_TERMINATED);
			} else if (cJSON_IsArray(f) || cJSON_IsObject(f)) {
				char *s = cJSON_PrintUnformatted(f);
				if (s) {
					curl_mimepart *part = curl_mime_addpart(mime);
					curl_mime_name(part, f->string);
					curl_mime_data(part, s, CURL_ZERO_TERMINATED);
					free(s);
				}
			}
			f = f->next;
		}
	}
	/* add file parts: files can be array of {name:<fieldname>, path:<filepath>} or simple strings (field name 'file') */
	if (files && cJSON_IsArray(files)) {
		cJSON *fi = NULL; int idx = 0;
		cJSON_ArrayForEach(fi, files) {
			const char *fieldname = "file";
			const char *path = NULL;
			if (cJSON_IsString(fi)) path = fi->valuestring;
			else if (cJSON_IsObject(fi)) {
				cJSON *pn = cJSON_GetObjectItemCaseSensitive(fi, "path");
				cJSON *fn = cJSON_GetObjectItemCaseSensitive(fi, "name");
				if (cJSON_IsString(pn)) path = pn->valuestring;
				if (cJSON_IsString(fn)) fieldname = fn->valuestring;
			}
			if (!path) continue;
			curl_mimepart *part = curl_mime_addpart(mime);
			curl_mime_name(part, fieldname);
			curl_mime_filedata(part, path);
			idx++;
		}
	}

	curl_easy_setopt(curl, CURLOPT_MIMEPOST, mime);
	curl_easy_setopt(curl, CURLOPT_WRITEFUNCTION, write_cb);
	curl_easy_setopt(curl, CURLOPT_WRITEDATA, (void *)resp);
	CURLcode rc = curl_easy_perform(curl);
	long code = 0; curl_easy_getinfo(curl, CURLINFO_RESPONSE_CODE, &code);
	curl_mime_free(mime);
	curl_slist_free_all(hdrs);
	curl_easy_cleanup(curl);
	if (rc != CURLE_OK) return 3;
	if (code >= 400) return (int)code;
	return 0;
}

/* Parse API JSON response and save image to outpath. Returns 0 on success. */
int save_image_from_api_response(const char *resp_buf, const char *outpath, const char *api_key) {
	if (!resp_buf) return 1;
	cJSON *root = cJSON_Parse(resp_buf);
	if (!root) return 2;
	cJSON *data = cJSON_GetObjectItemCaseSensitive(root, "data");
	cJSON *first = NULL;
	if (cJSON_IsArray(data)) first = cJSON_GetArrayItem(data, 0);
	else first = data;
	char *b64 = NULL;
	if (first) {
		cJSON *b64item = cJSON_GetObjectItemCaseSensitive(first, "b64_json");
		if (cJSON_IsString(b64item)) b64 = strdup(b64item->valuestring);
		if (!b64) {
			cJSON *imgitem = cJSON_GetObjectItemCaseSensitive(first, "image");
			if (cJSON_IsString(imgitem)) b64 = strdup(imgitem->valuestring);
		}
		if (!b64) {
			cJSON *urlitem = cJSON_GetObjectItemCaseSensitive(first, "url");
			if (cJSON_IsString(urlitem)) b64 = strdup(urlitem->valuestring);
		}
	}
	if (!b64) { cJSON_Delete(root); return 3; }
	int final_rc = 0;
	if (strncmp(b64, "http", 4) == 0) {
		struct membuf r2 = { .buf = NULL, .len = 0 };
		int rc = http_fetch_binary(b64, api_key, &r2);
		if (rc != 0) final_rc = 20 + rc;
		else final_rc = save_binary_file(outpath, (unsigned char*)r2.buf, r2.len);
		if (r2.buf) free(r2.buf);
	} else {
		size_t outlen = 0;
		unsigned char *decoded = base64_decode(b64, strlen(b64), &outlen);
		if (!decoded) { final_rc = 7; }
		else { final_rc = save_binary_file(outpath, decoded, outlen); free(decoded); }
	}
	free(b64);
	cJSON_Delete(root);
	return final_rc;
}

/* minimal base64 decode implementation */
unsigned char *base64_decode(const char *data, size_t input_length, size_t *out_len) {
	unsigned char dtable[256];
	memset(dtable, 0x80, 256);
	for (int i = 0; i < 64; i++) dtable[(unsigned char)"ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/"[i]] = (unsigned char)i;
	unsigned char *out = malloc((input_length * 3) / 4 + 4);
	if (!out) return NULL;
	unsigned char *pos = out;
	unsigned int val = 0; int valb = -8;
	for (size_t i = 0; i < input_length; i++) {
		unsigned char c = data[i];
		if (isspace(c) || c == '=') break;
		unsigned char d = dtable[c];
		if (d & 0x80) continue;
		val = (val << 6) | d;
		valb += 6;
		if (valb >= 0) {
			*pos++ = (unsigned char)((val >> valb) & 0xFF);
			valb -= 8;
		}
	}
	*out_len = pos - out;
	return out;
}

int generate_and_save(const char *api_key, const char *prompt, int w, int h, const char *outpath, const char *extra_body_json) {
	const char *url = "https://external.api.recraft.ai/v1/images/generations";
	struct membuf resp = { .buf = NULL, .len = 0 };

	/* Build payload using cJSON so we can merge extra_body safely */
	cJSON *req = cJSON_CreateObject();
	if (!req) { fprintf(stderr, "cJSON allocation failed\n"); return 9; }
	cJSON_AddStringToObject(req, "prompt", prompt ? prompt : "");
	cJSON_AddNumberToObject(req, "n", 1);
	const char *model = getenv("RECRAFT_MODEL");
	if (!model) model = "recraftv4";
	cJSON_AddStringToObject(req, "model", model);
	const char *resp_fmt = getenv("RECRAFT_RESPONSE_FORMAT");
	if (!resp_fmt) resp_fmt = "b64_json";
	cJSON_AddStringToObject(req, "response_format", resp_fmt);
	char size_str[64] = "1024x1024";
	if (w > 0 && h > 0) snprintf(size_str, sizeof(size_str), "%dx%d", w, h);
	cJSON_AddStringToObject(req, "size", size_str);

	/* merge extra_body_json if provided */
	if (extra_body_json) {
		cJSON *extra = cJSON_Parse(extra_body_json);
		if (extra) {
			cJSON *child = extra->child;
			while (child) {
				/* if same key exists, replace it */
				cJSON *existing = cJSON_GetObjectItemCaseSensitive(req, child->string);
				if (existing) cJSON_ReplaceItemInObjectCaseSensitive(req, child->string, cJSON_Duplicate(child, 1));
				else cJSON_AddItemToObject(req, child->string, cJSON_Duplicate(child, 1));
				child = child->next;
			}
			cJSON_Delete(extra);
		} else {
			fprintf(stderr, "Warning: failed to parse extra_body_json, ignoring.\n");
		}
	}

	char *payload = cJSON_PrintUnformatted(req);
	if (!payload) { cJSON_Delete(req); fprintf(stderr, "Failed to serialize JSON payload\n"); return 10; }

	int rc = http_post_json(url, api_key, payload, &resp);
	if (rc != 0) {
		fprintf(stderr, "HTTP POST failed: %d\n", rc);
		if (resp.buf) free(resp.buf);
		free(payload);
		cJSON_Delete(req);
		return rc;
	}
	int save_rc = save_image_from_api_response(resp.buf, outpath, api_key);
	if (resp.buf) free(resp.buf);
	free(payload);
	cJSON_Delete(req);
	return save_rc;
}

int run_manifest(const char *manifest_path) {
	char *txt = read_file_to_string(manifest_path);
	if (!txt) { fprintf(stderr, "Failed to read manifest: %s\n", manifest_path); return 2; }
	cJSON *root = cJSON_Parse(txt);
	if (!root) { fprintf(stderr, "Manifest JSON parse error.\n"); free(txt); return 3; }
	if (!cJSON_IsArray(root)) { fprintf(stderr, "Manifest must be a JSON array.\n"); cJSON_Delete(root); free(txt); return 4; }

	const char *api_key = getenv("RECRAFT_API_KEY");
	if (!api_key) { fprintf(stderr, "RECRAFT_API_KEY not set.\n"); cJSON_Delete(root); free(txt); return 5; }

	cJSON *item = NULL; int idx = 0;
	cJSON_ArrayForEach(item, root) {
		cJSON *name = cJSON_GetObjectItemCaseSensitive(item, "name");
		cJSON *prompt = cJSON_GetObjectItemCaseSensitive(item, "prompt");
		cJSON *w = cJSON_GetObjectItemCaseSensitive(item, "w");
		cJSON *h = cJSON_GetObjectItemCaseSensitive(item, "h");
		cJSON *out = cJSON_GetObjectItemCaseSensitive(item, "out");
		if (!cJSON_IsString(prompt) || !cJSON_IsNumber(w) || !cJSON_IsNumber(h) || !cJSON_IsString(out)) {
			fprintf(stderr, "Manifest entry %d invalid, skipping.\n", idx);
			idx++; continue;
		}
		printf("Generating %s -> %s (%d x %d)\n", cJSON_IsString(name)?name->valuestring:"(anon)", out->valuestring, w->valueint, h->valueint);
		/* support optional extra_body object in manifest */
		cJSON *extra = cJSON_GetObjectItemCaseSensitive(item, "extra_body");
		/* support optional endpoint override and files for multipart */
		cJSON *endpoint_item = cJSON_GetObjectItemCaseSensitive(item, "endpoint");
		const char *endpoint = cJSON_IsString(endpoint_item) ? endpoint_item->valuestring : "/images/generations";
		/* allow manifest to pass files array for multipart endpoints */
		cJSON *files = cJSON_GetObjectItemCaseSensitive(item, "files");
		if (files && cJSON_IsArray(files)) {
			/* multipart request */
			char urlbuf[1024]; snprintf(urlbuf, sizeof(urlbuf), "https://external.api.recraft.ai/v1%s", endpoint);
			struct membuf resp2 = { .buf = NULL, .len = 0 };
			int rc = http_post_multipart(urlbuf, getenv("RECRAFT_API_KEY"), extra, files, &resp2);
			if (rc != 0) { fprintf(stderr, "Multipart POST failed: %d\n", rc); if (resp2.buf) free(resp2.buf); cJSON_Delete(root); free(txt); return rc; }
			int s = save_image_from_api_response(resp2.buf, out->valuestring, getenv("RECRAFT_API_KEY"));
			if (resp2.buf) free(resp2.buf);
			if (s != 0) { fprintf(stderr, "Saving multipart response failed for %s (err=%d).\n", out->valuestring, s); cJSON_Delete(root); free(txt); return s; }
		} else {
			/* JSON-based generation */
			char *extra_str = NULL;
			if (extra) extra_str = cJSON_PrintUnformatted(extra);
			int r = generate_and_save(getenv("RECRAFT_API_KEY"), prompt->valuestring, w->valueint, h->valueint, out->valuestring, extra_str);
			if (extra_str) free(extra_str);
			if (r != 0) { fprintf(stderr, "Generation failed for %s (err=%d). Stopping.\n", out->valuestring, r); cJSON_Delete(root); free(txt); return r; }
		}
		idx++;
	}

	cJSON_Delete(root);
	free(txt);
	return 0;
}

int main(int argc, char **argv) {
	if (argc >= 3 && strcmp(argv[1], "--manifest") == 0) {
		return run_manifest(argv[2]);
	}
	if (argc < 4) {
		fprintf(stderr, "Usage: %s <prompt> <width> <height> [output.png]  OR  %s --manifest manifest.json\n", argv[0], argv[0]);
		return 1;
	}
	const char *prompt = argv[1];
	int w = atoi(argv[2]);
	int h = atoi(argv[3]);
	const char *outpath = (argc >=5) ? argv[4] : "out.png";
	const char *api_key = getenv("RECRAFT_API_KEY");
	if (!api_key) { fprintf(stderr, "RECRAFT_API_KEY not set in environment.\n"); return 2; }
	return generate_and_save(api_key, prompt, w, h, outpath, NULL);
}
