#ifndef BLASTMONIDZ_BRIDGE_H
#define BLASTMONIDZ_BRIDGE_H

void blastmonidz_bridge_init(void);
void blastmonidz_bridge_shutdown(void);
void blastmonidz_bridge_poll(void);
void blastmonidz_bridge_publish_status(const char *channel, const char *message);

const char *blastmonidz_bridge_latest_status(void);
const char *blastmonidz_bridge_latest_inbox(void);
const char *blastmonidz_bridge_inbox_path(void);
const char *blastmonidz_bridge_outbox_path(void);

#endif