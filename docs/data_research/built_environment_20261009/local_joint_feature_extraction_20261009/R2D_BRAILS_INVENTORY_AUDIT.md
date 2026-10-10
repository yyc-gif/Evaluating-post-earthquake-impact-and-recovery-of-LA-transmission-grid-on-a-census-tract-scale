# Existing Windows R2D / BRAILS inventory audit

The prior D: drive is not mounted. The installation exists at `C:\Users\yinch\Downloads\R2D_Windows_Download\R2D_Windows_Download`. It includes runBrails.py and model/example files, not a completed countywide building attribute census.

The archived CE294 project files were found outside the initial 2025 search roots at `C:\2024-2025 Fall\CIV ENG 294 - Disaster Risk Analysis of Infrastructure Systems\05_Project\Project_Files`. The source report describes FEMA USA Structures / National Structure Inventory obtained through BRAILS. Per-field observed-versus-predicted lineage is not retained; no school YearBuilt or StructureType is admitted as an observed countywide variable.

| file | records | tracts intersected | identity duplicates | source/coverage |
|---|---:|---:|---:|---|
| C:\2024-2025 Fall\CIV ENG 294 - Disaster Risk Analysis of Infrastructure Systems\05_Project\Project_Files\1-Merged_School_Data_with_All_Attributes(1).csv | 884 | 450 | 0 | LAUSD school portfolio; estimates/derived attributes |
| C:\2024-2025 Fall\CIV ENG 294 - Disaster Risk Analysis of Infrastructure Systems\05_Project\Project_Files\Long Beach Result.xlsx | 884 | 450 | 0 | LAUSD school portfolio; estimates/derived attributes |
| C:\2024-2025 Fall\CIV ENG 294 - Disaster Risk Analysis of Infrastructure Systems\05_Project\Project_Files\Merged_School_Data_with_All_Attributes.csv | 884 | 432 | 0 | LAUSD school portfolio; estimates/derived attributes |
| C:\2024-2025 Fall\CIV ENG 294 - Disaster Risk Analysis of Infrastructure Systems\05_Project\Project_Files\Merged_School_Data_with_All_Attributes.xlsx | 884 | 432 | 0 | LAUSD school portfolio; estimates/derived attributes |
| C:\2024-2025 Fall\CIV ENG 294 - Disaster Risk Analysis of Infrastructure Systems\05_Project\Project_Files\Northridge Result.xlsx | 884 | 450 | 0 | LAUSD school portfolio; estimates/derived attributes |
| C:\2024-2025 Fall\CIV ENG 294 - Disaster Risk Analysis of Infrastructure Systems\05_Project\Project_Files\NRI_Shapefile_CensusTracts\Long Beach Result.xlsx | 884 | 450 | 0 | LAUSD school portfolio; estimates/derived attributes |
| C:\2024-2025 Fall\CIV ENG 294 - Disaster Risk Analysis of Infrastructure Systems\05_Project\Project_Files\San Fernando Result.xlsx | 884 | 450 | 0 | LAUSD school portfolio; estimates/derived attributes |

All three hazard XLSX files are R2D school simulation outputs, not assessor observations or new physical hazard inputs. The 884-record portfolios do not support countywide structural taxonomy or all-use building age. Exact hashes, field completeness, duplicates and tract intersection coverage are in companion tables. LARIAC6 provides independent observed roof geometry; school attributes are not propagated to its millions of buildings. No API/image predictions or new R2D analysis was run.
