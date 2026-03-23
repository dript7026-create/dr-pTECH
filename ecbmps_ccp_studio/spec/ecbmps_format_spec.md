# ECBMPS File Format Specification v1
# Electronic Colour Book Media Playback Shell

## Overview
ECBMPS is a binary container for rich paged media books with persistent
reader state (bookmarks, passage highlights).  It does NOT contain
in-page gameplay — that role is filled by the sibling CCP format.

## Header (40 bytes, little-endian)
| Offset | Size | Field              | Notes                              |
|--------|------|--------------------|------------------------------------|
| 0      | 4    | magic              | `ECBM` (0x45 0x43 0x42 0x4D)      |
| 4      | 4    | version            | uint32, currently `1`              |
| 8      | 4    | page_count         | uint32                             |
| 12     | 4    | flags              | bit 0: has_toc, bit 1: has_cover   |
| 16     | 8    | title_offset       | uint64 — byte offset of title      |
| 24     | 8    | toc_offset         | uint64 — byte offset of TOC        |
| 32     | 8    | userdata_offset    | uint64 — byte offset of user data  |

## Title Section
| Size | Field           |
|------|-----------------|
| 4    | title_length    |
| var  | title (UTF-8)   |
| 4    | author_length   |
| var  | author (UTF-8)  |

## Table of Contents (page_count entries)
Each entry is 16 bytes:
| Size | Field       | Notes                               |
|------|-------------|-------------------------------------|
| 8    | page_offset | uint64 — absolute byte offset       |
| 4    | page_size   | uint32 — byte size of page blob     |
| 1    | page_type   | 0=text, 1=image, 2=combined         |
| 1    | flags       | bit 0: has_images_inline            |
| 2    | reserved    |                                     |

## Page Data

### Text Page (type 0)
| Size | Field        |
|------|--------------|
| 4    | text_length  |
| var  | text (UTF-8) |

### Image Page (type 1)
| Size | Field         |
|------|---------------|
| 1    | image_format  | 0=raw RGBA, 1=PNG, 2=JPEG          |
| 4    | image_width   |
| 4    | image_height  |
| 4    | image_length  | byte length of compressed payload   |
| var  | image_data    |

### Combined Page (type 2)
| Size | Field         |
|------|---------------|
| 4    | text_length   |
| var  | text (UTF-8)  |
| 1    | image_count   |
Per embedded image:
| Size | Field         |
|------|---------------|
| 1    | image_format  |
| 2    | layout_x      | int16 — pixel offset                |
| 2    | layout_y      | int16                               |
| 2    | layout_w      | int16                               |
| 2    | layout_h      | int16                               |
| 4    | image_length  |
| var  | image_data    |

## User Data Section (persistent reader memory)
| Size | Field            |
|------|------------------|
| 4    | userdata_magic   | `ECBU` (0x45 0x43 0x42 0x55)       |
| 2    | bookmark_count   |
Per bookmark:
| Size | Field            |
|------|------------------|
| 4    | page_index       |
| 4    | scroll_offset    |
| 1    | label_length     |
| var  | label (UTF-8)    |
| 2    | highlight_count  |
Per highlight:
| Size | Field            |
|------|------------------|
| 4    | page_index       |
| 4    | start_char       |
| 4    | end_char         |
| 4    | color_rgba       |

## File Extension
`.ecbmps`

## MIME Type
`application/x-ecbmps`
