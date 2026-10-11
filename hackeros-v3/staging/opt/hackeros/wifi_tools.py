"""Parse NetworkManager's escaped terse output without breaking SSIDs."""


def split_fields(line):
    fields, value, escaped = [], [], False
    for char in line:
        if escaped:
            value.append(char)
            escaped = False
        elif char == "\\":
            escaped = True
        elif char == ":":
            fields.append("".join(value))
            value = []
        else:
            value.append(char)
    if escaped:
        value.append("\\")
    return fields + ["".join(value)]


def parse_networks(output):
    networks = {}
    for line in output.splitlines():
        fields = split_fields(line)
        if len(fields) != 4 or not fields[1]:
            continue
        active, ssid, signal, security = fields
        try:
            signal = max(0, min(100, int(signal)))
        except ValueError:
            continue
        entry = {"ssid": ssid, "signal": signal, "security": security,
                 "active": active == "*"}
        if ssid not in networks or signal > networks[ssid]["signal"] or entry["active"]:
            networks[ssid] = entry
    return sorted(networks.values(), key=lambda item: (not item["active"], -item["signal"], item["ssid"]))
