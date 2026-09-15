"""Open Data Export Packager.

Prepares and exports clean, standardized open data tables (JSON, Parquet)
for community inspection, research, and reproducibility.
"""

from pathlib import Path

import polars as pl


class OpenDataPackager:
    """Exports consolidated competition datasets to outputs/open_data/."""

    def __init__(self, export_dir: str = "outputs/open_data") -> None:
        self.export_dir = Path(export_dir)
        self.export_dir.mkdir(parents=True, exist_ok=True)

    def export_all(
        self,
        scores_dir: str = "outputs/scores",
    ) -> dict[str, str]:
        """Export all generated analytical scores to the open data folder.

        Returns:
            Dictionary mapping exported filename to its destination path.
        """
        src = Path(scores_dir)
        exported: dict[str, str] = {}

        # 1. Copy JSON rankings
        rank_json = src / "player_value_rankings.json"
        if rank_json.exists():
            dest = self.export_dir / "fspv_player_rankings.json"
            dest.write_bytes(rank_json.read_bytes())
            exported["rankings_json"] = str(dest)

        # 2. Export Parquet rankings
        if rank_json.exists():
            try:
                df = pl.read_json(rank_json)
                dest_p = self.export_dir / "fspv_player_rankings.parquet"
                df.write_parquet(dest_p)
                exported["rankings_parquet"] = str(dest_p)
            except Exception:
                pass

        # 3. Copy validation report
        val_json = src / "validation_report.json"
        if val_json.exists():
            dest_val = self.export_dir / "external_validation_audit.json"
            dest_val.write_bytes(val_json.read_bytes())
            exported["validation_json"] = str(dest_val)

        # 4. Write Open Data Manifest & Data Dictionary
        manifest_path = self.export_dir / "README.md"
        manifest_text = """# SkillCorner Open Data Basketball — Full Spectrum Player Value Export Pack

This directory contains standardized, open analytical outputs for external researchers, scouts, and community validation.

## Files Included

1. **`fspv_player_rankings.json` / `.parquet`**:
   - `player_id`: Canonical player identifier (resolved via `player_id_aliases.csv`).
   - `player_name`: Full athlete name.
   - `team`: Official ACB club name.
   - `position`: Guard / Forward / Center role.
   - `bav_score`: Standardized Ball Action Value z-score (mean=0, std=1).
   - `sci_score`: Standardized Space Creation Index z-score (mean=0, std=1).
   - `fspv_score`: Combined metric = 0.5 * BAV_z + 0.5 * SCI_z.
   - `fspv_percentile`: Percentile rank across evaluated cohort (0.0% to 100.0%).

2. **`external_validation_audit.json`**:
   - Spearman rank correlations vs 293-game season aggregates (`points_per_shot`, `handler_ppp`).
   - Face validity top 5 athletes with tactical justification.

## Reproducibility
All files were generated deterministically via:
```bash
python -m presentation.cli run-all
```
"""
        manifest_path.write_text(manifest_text, encoding="utf-8")
        exported["manifest"] = str(manifest_path)

        return exported
