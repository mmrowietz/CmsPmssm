from pathlib import Path

INFILE = Path("datacards/provided/SUS_20_001/T6bbllslepton_800_150.txt")
OUTFILE = Path("datacards/provided/SUS_20_001/template_card.txt")

text = INFILE.read_text()
lines = text.splitlines()

# Parse process layout from the first two "process" lines after the long bin/process block
process_name_line_idx = None
process_id_line_idx = None
for i, line in enumerate(lines):
    if line.startswith("process"):
        parts = line.split()
        if len(parts) > 1 and any(tok.isalpha() or tok == "SUSY" for tok in parts[1:]):
            process_name_line_idx = i
            process_id_line_idx = i + 1
            break

if process_name_line_idx is None:
    raise RuntimeError("Could not find process lines")

proc_names = lines[process_name_line_idx].split()[1:]

# Replace SUSY rates with placeholders _SR_1 ... _SR_28
rate_idx = None
for i, line in enumerate(lines):
    if line.startswith("rate"):
        rate_idx = i
        break

if rate_idx is None:
    raise RuntimeError("Could not find rate line")

rate_parts = lines[rate_idx].split()
new_rate = ["rate"]
sr_counter = 1
for pname, value in zip(proc_names, rate_parts[1:]):
    if pname == "SUSY":
        new_rate.append(f"_SR_{sr_counter}")
        sr_counter += 1
    else:
        new_rate.append(value)
lines[rate_idx] = "  ".join(new_rate)

# Rename SUSY -> Signal in the process-name line
proc_name_parts = lines[process_name_line_idx].split()
proc_name_parts = [("Signal" if tok == "SUSY" else tok) for tok in proc_name_parts]
lines[process_name_line_idx] = "  ".join(proc_name_parts)

# Drop signal systematics, but KEEP gmN rows (signal stat uncertainties may be gmN)
# Rule: if a nuisance line touches only Signal columns and is not gmN, remove it
new_lines = []
for i, line in enumerate(lines):
    stripped = line.strip()
    if not stripped or stripped.startswith("#"):
        new_lines.append(line)
        continue

    parts = line.split()
    if len(parts) < 3:
        new_lines.append(line)
        continue

    nuisance_name = parts[0]
    nuisance_type = parts[1]

    if nuisance_name in {"imax", "jmax", "kmax", "bin", "observation", "process", "rate"}:
        new_lines.append(line)
        continue
    if nuisance_name == "shapes":
        new_lines.append(line)
        continue
    if nuisance_type not in {"lnN", "gmN", "shape", "shapeN2", "lnU"}:
        new_lines.append(line)
        continue

    # For gmN, skip the count token before the per-process payload
    payload = parts[3:] if nuisance_type == "gmN" else parts[2:]
    if len(payload) != len(proc_names):
        new_lines.append(line)
        continue

    touches_signal = False
    touches_background = False
    for pname, entry in zip(proc_names, payload):
        if entry == "-":
            continue
        if pname == "SUSY":
            touches_signal = True
        else:
            touches_background = True

    # remove pure signal systematic rows unless gmN
    if touches_signal and not touches_background and nuisance_type != "gmN":
        continue

    new_lines.append(line)

OUTFILE.write_text("\n".join(new_lines) + "\n")
print(f"[wrote] {OUTFILE}")
