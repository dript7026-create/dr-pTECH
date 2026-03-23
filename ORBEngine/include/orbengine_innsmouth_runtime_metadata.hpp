#ifndef ORBENGINE_INNSMOUTH_RUNTIME_METADATA_HPP
#define ORBENGINE_INNSMOUTH_RUNTIME_METADATA_HPP

namespace innsmouth_runtime
{
inline int readTextFile(const char *path, std::string &contents)
{
    FILE *file = fopen(path, "rb");
    if (!file)
    {
        return 0;
    }
    if (fseek(file, 0, SEEK_END) != 0)
    {
        fclose(file);
        return 0;
    }
    long fileSize = ftell(file);
    if (fileSize < 0)
    {
        fclose(file);
        return 0;
    }
    rewind(file);
    contents.resize((size_t)fileSize);
    if (fileSize > 0 && fread(contents.data(), 1, (size_t)fileSize, file) != (size_t)fileSize)
    {
        fclose(file);
        contents.clear();
        return 0;
    }
    fclose(file);
    return 1;
}

inline int loadFirstExistingTextFile(const char *const *paths, int pathCount, std::string &contents)
{
    for (int index = 0; index < pathCount; ++index)
    {
        if (readTextFile(paths[index], contents))
        {
            return 1;
        }
    }
    return 0;
}

inline size_t findJsonKey(const std::string &text, const char *key, size_t start = 0)
{
    std::string needle = "\"";
    needle += key;
    needle += "\"";
    return text.find(needle, start);
}

inline size_t findJsonValueStart(const std::string &text, size_t keyPos)
{
    size_t colonPos = text.find(':', keyPos);
    if (colonPos == std::string::npos)
    {
        return std::string::npos;
    }
    return text.find_first_not_of(" \t\r\n", colonPos + 1);
}

inline size_t findMatchingJsonToken(const std::string &text, size_t start, char openToken, char closeToken)
{
    int depth = 0;
    int inString = 0;
    int escaped = 0;
    for (size_t index = start; index < text.size(); ++index)
    {
        char value = text[index];
        if (inString)
        {
            if (escaped)
            {
                escaped = 0;
            }
            else if (value == '\\')
            {
                escaped = 1;
            }
            else if (value == '"')
            {
                inString = 0;
            }
            continue;
        }
        if (value == '"')
        {
            inString = 1;
            continue;
        }
        if (value == openToken)
        {
            ++depth;
            continue;
        }
        if (value == closeToken)
        {
            --depth;
            if (depth == 0)
            {
                return index;
            }
        }
    }
    return std::string::npos;
}

inline int extractJsonObjectForKey(const std::string &text, const char *key, std::string &objectText)
{
    size_t keyPos = findJsonKey(text, key);
    if (keyPos == std::string::npos)
    {
        return 0;
    }
    size_t valuePos = findJsonValueStart(text, keyPos);
    if (valuePos == std::string::npos || text[valuePos] != '{')
    {
        return 0;
    }
    size_t endPos = findMatchingJsonToken(text, valuePos, '{', '}');
    if (endPos == std::string::npos)
    {
        return 0;
    }
    objectText = text.substr(valuePos, endPos - valuePos + 1);
    return 1;
}

inline int extractJsonArrayForKey(const std::string &text, const char *key, std::string &arrayText)
{
    size_t keyPos = findJsonKey(text, key);
    if (keyPos == std::string::npos)
    {
        return 0;
    }
    size_t valuePos = findJsonValueStart(text, keyPos);
    if (valuePos == std::string::npos || text[valuePos] != '[')
    {
        return 0;
    }
    size_t endPos = findMatchingJsonToken(text, valuePos, '[', ']');
    if (endPos == std::string::npos)
    {
        return 0;
    }
    arrayText = text.substr(valuePos, endPos - valuePos + 1);
    return 1;
}

inline void collectJsonObjectEntries(const std::string &arrayText, std::vector<std::string> &objects)
{
    size_t index = 0;
    while (index < arrayText.size())
    {
        size_t start = arrayText.find('{', index);
        if (start == std::string::npos)
        {
            break;
        }
        size_t end = findMatchingJsonToken(arrayText, start, '{', '}');
        if (end == std::string::npos)
        {
            break;
        }
        objects.push_back(arrayText.substr(start, end - start + 1));
        index = end + 1;
    }
}

inline int parseFloatForKey(const std::string &text, const char *key, float &value)
{
    size_t keyPos = findJsonKey(text, key);
    if (keyPos == std::string::npos)
    {
        return 0;
    }
    size_t valuePos = findJsonValueStart(text, keyPos);
    if (valuePos == std::string::npos)
    {
        return 0;
    }
    char *endPtr = NULL;
    value = std::strtof(text.c_str() + valuePos, &endPtr);
    return endPtr != text.c_str() + valuePos;
}

inline int parseIntForKey(const std::string &text, const char *key, int &value)
{
    size_t keyPos = findJsonKey(text, key);
    if (keyPos == std::string::npos)
    {
        return 0;
    }
    size_t valuePos = findJsonValueStart(text, keyPos);
    if (valuePos == std::string::npos)
    {
        return 0;
    }
    char *endPtr = NULL;
    long parsed = std::strtol(text.c_str() + valuePos, &endPtr, 10);
    if (endPtr == text.c_str() + valuePos)
    {
        return 0;
    }
    value = (int)parsed;
    return 1;
}

inline int parseStringForKey(const std::string &text, const char *key, std::string &value)
{
    size_t keyPos = findJsonKey(text, key);
    if (keyPos == std::string::npos)
    {
        return 0;
    }
    size_t valuePos = findJsonValueStart(text, keyPos);
    if (valuePos == std::string::npos || text[valuePos] != '"')
    {
        return 0;
    }

    value.clear();
    int escaped = 0;
    for (size_t index = valuePos + 1; index < text.size(); ++index)
    {
        char current = text[index];
        if (escaped)
        {
            value.push_back(current);
            escaped = 0;
        }
        else if (current == '\\')
        {
            escaped = 1;
        }
        else if (current == '"')
        {
            return 1;
        }
        else
        {
            value.push_back(current);
        }
    }
    value.clear();
    return 0;
}

inline void deriveEnvironmentAnchors(EnvironmentRenderProfile &profile)
{
    profile.anchors[0] = {-profile.silhouette.radiusX, -profile.silhouette.radiusY, 0.0f};
    profile.anchors[1] = {profile.silhouette.radiusX, -profile.silhouette.radiusY, 0.0f};
    profile.anchors[2] = {profile.silhouette.radiusX, profile.silhouette.radiusY, profile.topLift};
    profile.anchors[3] = {-profile.silhouette.radiusX, profile.silhouette.radiusY, profile.topLift};
}

inline int parseAttachmentSocketObject(const std::string &text, AttachmentSocket &socket)
{
    return parseFloatForKey(text, "u", socket.u) &&
           parseFloatForKey(text, "v", socket.v) &&
           parseFloatForKey(text, "z", socket.z);
}

inline int parseAttachmentMapObject(const std::string &text, PlayerAttachmentMap &map, const char *const *socketNames, int socketCount)
{
    for (int index = 0; index < socketCount; ++index)
    {
        std::string socketObject;
        if (!extractJsonObjectForKey(text, socketNames[index], socketObject) ||
            !parseAttachmentSocketObject(socketObject, map.sockets[index]))
        {
            return 0;
        }
    }
    return 1;
}

inline int parseEnvironmentProfileObject(const std::string &text, int &type, EnvironmentRenderProfile &profile)
{
    if (!parseIntForKey(text, "type", type) ||
        !parseFloatForKey(text, "topLift", profile.topLift) ||
        !parseFloatForKey(text, "shadowWidth", profile.shadowWidth) ||
        !parseFloatForKey(text, "shadowDepth", profile.shadowDepth))
    {
        return 0;
    }

    std::string silhouetteObject;
    if (!extractJsonObjectForKey(text, "silhouette", silhouetteObject) ||
        !parseFloatForKey(silhouetteObject, "radiusX", profile.silhouette.radiusX) ||
        !parseFloatForKey(silhouetteObject, "radiusY", profile.silhouette.radiusY) ||
        !parseFloatForKey(silhouetteObject, "occlusionDepth", profile.silhouette.occlusionDepth))
    {
        return 0;
    }

    std::string anchorsArray;
    if (extractJsonArrayForKey(text, "anchors", anchorsArray))
    {
        std::vector<std::string> anchorObjects;
        collectJsonObjectEntries(anchorsArray, anchorObjects);
        if (anchorObjects.size() == 4)
        {
            for (int index = 0; index < 4; ++index)
            {
                if (!parseFloatForKey(anchorObjects[index], "x", profile.anchors[index].x) ||
                    !parseFloatForKey(anchorObjects[index], "y", profile.anchors[index].y) ||
                    !parseFloatForKey(anchorObjects[index], "z", profile.anchors[index].z))
                {
                    deriveEnvironmentAnchors(profile);
                    return 1;
                }
            }
            return 1;
        }
    }

    deriveEnvironmentAnchors(profile);
    return 1;
}

inline EnvironmentRenderProfile scaleEnvironmentRenderProfile(const EnvironmentRenderProfile &profile, float objectScale)
{
    float scaleValue = objectScale;
    if (scaleValue < 0.80f)
    {
        scaleValue = 0.80f;
    }
    else if (scaleValue > 1.40f)
    {
        scaleValue = 1.40f;
    }
    EnvironmentRenderProfile scaled = profile;
    scaled.topLift *= scaleValue;
    scaled.shadowWidth *= scaleValue;
    scaled.shadowDepth *= scaleValue;
    scaled.silhouette.radiusX *= scaleValue;
    scaled.silhouette.radiusY *= scaleValue;
    scaled.silhouette.occlusionDepth *= scaleValue;
    for (int index = 0; index < 4; ++index)
    {
        scaled.anchors[index].x *= scaleValue;
        scaled.anchors[index].y *= scaleValue;
        scaled.anchors[index].z *= scaleValue;
    }
    return scaled;
}

inline void copyPlacementKey(char *destination, size_t destinationCount, const char *source)
{
    if (!destination || destinationCount == 0)
    {
        return;
    }
    if (!source)
    {
        destination[0] = 0;
        return;
    }
    std::strncpy(destination, source, destinationCount - 1);
    destination[destinationCount - 1] = 0;
}

inline int findEnvironmentPlacementProfile(const RuntimeEnvironmentMetadata &metadata, const char *placementKey)
{
    if (!placementKey || !placementKey[0])
    {
        return -1;
    }
    for (int index = 0; index < metadata.placementCount; ++index)
    {
        if (metadata.placementProfileLoaded[index] && std::strcmp(metadata.placementKeys[index], placementKey) == 0)
        {
            return index;
        }
    }
    return -1;
}

inline int loadAttachmentMetadataFromJson(
    const char *const *searchPaths,
    int pathCount,
    const char *const *socketNames,
    int socketCount,
    RuntimeAttachmentMetadata &metadata,
    int armorCount,
    int weaponCount)
{
    if (metadata.loaded)
    {
        return 1;
    }

    std::string text;
    if (!loadFirstExistingTextFile(searchPaths, pathCount, text))
    {
        return 0;
    }

    std::string runtimeProfiles;
    std::string baseSockets;
    if (!extractJsonObjectForKey(text, "runtime_profiles", runtimeProfiles) ||
        !extractJsonObjectForKey(runtimeProfiles, "base_sockets", baseSockets))
    {
        return 0;
    }

    if (!parseAttachmentMapObject(baseSockets, metadata.baseMap, socketNames, socketCount))
    {
        return 0;
    }

    std::string armorProfilesArray;
    if (extractJsonArrayForKey(runtimeProfiles, "armor_profiles", armorProfilesArray))
    {
        std::vector<std::string> armorObjects;
        collectJsonObjectEntries(armorProfilesArray, armorObjects);
        for (size_t index = 0; index < armorObjects.size(); ++index)
        {
            int armorSet = -1;
            PlayerAttachmentMap map = metadata.baseMap;
            if (parseIntForKey(armorObjects[index], "armor_set", armorSet) &&
                armorSet >= 0 && armorSet < armorCount &&
                parseAttachmentMapObject(armorObjects[index], map, socketNames, socketCount))
            {
                metadata.armorProfiles[armorSet] = map;
                metadata.armorProfileLoaded[armorSet] = 1;
            }
        }
    }

    std::string meleeProfilesArray;
    if (extractJsonArrayForKey(runtimeProfiles, "melee_profiles", meleeProfilesArray))
    {
        std::vector<std::string> meleeObjects;
        collectJsonObjectEntries(meleeProfilesArray, meleeObjects);
        for (size_t index = 0; index < meleeObjects.size(); ++index)
        {
            int weaponIndex = -1;
            std::string socketObject;
            AttachmentSocket socket = {};
            if (parseIntForKey(meleeObjects[index], "weapon_index", weaponIndex) &&
                weaponIndex >= 0 && weaponIndex < weaponCount &&
                extractJsonObjectForKey(meleeObjects[index], "right_hand", socketObject) &&
                parseAttachmentSocketObject(socketObject, socket))
            {
                metadata.meleeProfiles[weaponIndex] = metadata.baseMap;
                metadata.meleeProfiles[weaponIndex].sockets[SOCKET_RIGHT_HAND] = socket;
                metadata.meleeProfileLoaded[weaponIndex] = 1;
            }
        }
    }

    std::string projectileProfilesArray;
    if (extractJsonArrayForKey(runtimeProfiles, "projectile_profiles", projectileProfilesArray))
    {
        std::vector<std::string> projectileObjects;
        collectJsonObjectEntries(projectileProfilesArray, projectileObjects);
        for (size_t index = 0; index < projectileObjects.size(); ++index)
        {
            int weaponIndex = -1;
            std::string socketObject;
            AttachmentSocket socket = {};
            if (parseIntForKey(projectileObjects[index], "weapon_index", weaponIndex) &&
                weaponIndex >= 0 && weaponIndex < weaponCount &&
                extractJsonObjectForKey(projectileObjects[index], "left_hand", socketObject) &&
                parseAttachmentSocketObject(socketObject, socket))
            {
                metadata.projectileProfiles[weaponIndex] = metadata.baseMap;
                metadata.projectileProfiles[weaponIndex].sockets[SOCKET_LEFT_HAND] = socket;
                metadata.projectileProfileLoaded[weaponIndex] = 1;
            }
        }
    }

    metadata.loaded = 1;
    return 1;
}

inline int loadEnvironmentMetadataFromJson(
    const char *const *searchPaths,
    int pathCount,
    RuntimeEnvironmentMetadata &metadata,
    int environmentCount)
{
    if (metadata.loaded)
    {
        return 1;
    }

    std::string text;
    if (!loadFirstExistingTextFile(searchPaths, pathCount, text))
    {
        return 0;
    }

    metadata.placementCount = 0;

    std::string profilesArray;
    if (!extractJsonArrayForKey(text, "profiles", profilesArray))
    {
        return 0;
    }

    std::vector<std::string> profileObjects;
    collectJsonObjectEntries(profilesArray, profileObjects);
    for (size_t index = 0; index < profileObjects.size(); ++index)
    {
        int type = -1;
        EnvironmentRenderProfile profile = {};
        if (parseEnvironmentProfileObject(profileObjects[index], type, profile) &&
            type >= 0 && type < environmentCount)
        {
            metadata.profiles[type] = profile;
            metadata.profileLoaded[type] = 1;
        }
    }

    std::string placementsArray;
    if (extractJsonArrayForKey(text, "placements", placementsArray))
    {
        std::vector<std::string> placementObjects;
        collectJsonObjectEntries(placementsArray, placementObjects);
        for (size_t index = 0; index < placementObjects.size() && metadata.placementCount < environmentCount; ++index)
        {
            std::string key;
            int type = -1;
            EnvironmentRenderProfile profile = {};
            if (!parseStringForKey(placementObjects[index], "key", key) ||
                !parseEnvironmentProfileObject(placementObjects[index], type, profile))
            {
                continue;
            }
            copyPlacementKey(
                metadata.placementKeys[metadata.placementCount],
                sizeof(metadata.placementKeys[metadata.placementCount]),
                key.c_str());
            metadata.placementProfiles[metadata.placementCount] = profile;
            metadata.placementProfileLoaded[metadata.placementCount] = 1;
            metadata.placementCount += 1;
        }
    }

    metadata.loaded = 1;
    return 1;
}
} // namespace innsmouth_runtime

#endif