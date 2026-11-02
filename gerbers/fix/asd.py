import io
import zipfile
from pathlib import Path

# Folder containing your 3 exported truth files
TRUTH_DIR = Path("./files")

# Folder containing your badge .zip archives
ZIPS_DIR = Path("./zip")

# Extensions matching KiCad Protel export
PATTERNS = ("-F_Cu.gtl", "-F_Mask.gts", "-F_Paste.gtp")

def patch_zips_from_folder():
    # 1. Load the 3 truth files into memory as raw bytes
    truth_payloads = {}
    for pat in PATTERNS:
        match = next(TRUTH_DIR.glob(f"*{pat}"), None)
        if not match:
            print(f"[ERROR] Could not find any file ending with '{pat}' in {TRUTH_DIR}")
            return
        truth_payloads[pat] = match.read_bytes()
        print(f"[LOADED] {match.name} -> mapped to pattern '{pat}'")

    # 2. Iterate through all target zips
    target_zips = list(ZIPS_DIR.glob("*.zip"))
    if not target_zips:
        print(f"[WARN] No .zip files found in {ZIPS_DIR}")
        return

    for target_zip in target_zips:
        buffer = io.BytesIO()

        with zipfile.ZipFile(target_zip, "r") as zin:
            with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED) as zout:
                for item in zin.infolist():
                    # Identify if this entry matches one of our 3 layers
                    matched_pattern = next(
                        (pat for pat in PATTERNS if item.filename.endswith(pat)),
                        None
                    )

                    if matched_pattern:
                        # item preserves original filename, timestamp, and permissions
                        zout.writestr(item, truth_payloads[matched_pattern])
                        print(f"[{target_zip.name}] Injected {matched_pattern} into {item.filename}")
                    else:
                        # Copy silkscreen, edge cuts, drills untouched
                        zout.writestr(item, zin.read(item.filename))

        # Overwrite the zip in place
        target_zip.write_bytes(buffer.getvalue())
        print(f"[SUCCESS] Updated {target_zip.name}\n")

if __name__ == "__main__":
    patch_zips_from_folder()
