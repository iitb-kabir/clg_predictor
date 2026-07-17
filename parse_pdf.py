import fitz
import csv
import re

def extract_to_csv(pdf_path, csv_path):
    doc = fitz.open(pdf_path)
    records = []
    
    # State machine to parse lines
    # Expected fields: ROUND, RANK, CHOICE, INSTITUTE, COURSE, QUOTA, ALLOTTED_CAT, CAND_CAT, STATUS
    
    # We will gather all lines from all pages
    all_lines = []
    for page in doc:
        # Ignore headers/footers. We can just use the raw text lines.
        text = page.get_text()
        lines = text.split('\n')
        
        # Filter out header/footer lines
        for line in lines:
            line = line.strip()
            if not line:
                continue
            if "UR=Unreserved" in line or "PROVISIONAL SEAT ALLOTMENT" in line or "(WB UG MEDICAL" in line or line == "ROUND" or line == "ALL INDIA" or line == "RANK" or line == "CHOICE" or line == "NO." or line == "INSTITUTE" or line == "COURSE" or line == "ALLOTTED QUOTA" or line == "ALLOTTED" or line == "CATEGORY" or line == "CANDIDATE" or line == "STATUS":
                continue
            # Some pages have the page number at the bottom. It's usually just a number by itself, but so is round/rank.
            # Page numbers are usually at the end of the page text. Let's handle it later.
            all_lines.append(line)
            
    # Process lines into records
    idx = 0
    while idx < len(all_lines):
        try:
            # Check if this line is a page number (it usually appears right before the next page's header, or after status)
            # A record always starts with ROUND (1, 2, 3), followed by RANK (number).
            if all_lines[idx] in ["1", "2", "3"] and idx + 1 < len(all_lines) and all_lines[idx+1].isdigit() and len(all_lines[idx+1]) >= 4:
                # We found the start of a record!
                round_val = all_lines[idx]
                rank = all_lines[idx+1]
                choice = all_lines[idx+2]
                
                idx += 3
                
                # Institute can be multiple lines. It ends when we see "MBBS" or "BDS"
                inst_lines = []
                while idx < len(all_lines) and all_lines[idx] not in ["MBBS", "BDS"]:
                    inst_lines.append(all_lines[idx])
                    idx += 1
                
                institute = " ".join(inst_lines)
                course = all_lines[idx] if idx < len(all_lines) else ""
                idx += 1
                
                # Quota can be multiple lines (e.g. "Private", "Management", "Quota")
                quota_lines = []
                # It ends when we see a category like "UR", "SC", "OBC", "ST", "EWS"
                # Wait, categories can be complex like "OBC-A (Non-Creamy Layer)"
                # Let's collect lines until we see UR, SC, ST, OBC, EWS, or if quota_lines ends with "Quota"
                # Actually, "State Quota", "Private Management Quota", "NRI Quota"
                while idx < len(all_lines):
                    quota_lines.append(all_lines[idx])
                    joined_quota = " ".join(quota_lines)
                    if joined_quota in ["State Quota", "Private Management Quota", "NRI Quota"]:
                        idx += 1
                        break
                    if "Quota" in joined_quota:
                        idx += 1
                        break
                    idx += 1
                quota = " ".join(quota_lines)
                
                # Allotted Category
                # Can be multiple lines. Ends when next line is the Candidate Category.
                # Actually, status is always "Retained" or "Fresh Allotment" (which is 2 lines: "Fresh", "Allotment") or "Upgraded"
                # Let's work backwards from status.
                
                # We know the next lines contain Allotted Cat, Cand Cat, Status.
                # Let's grab all lines until we hit a valid Status.
                temp_lines = []
                while idx < len(all_lines):
                    if all_lines[idx] == "Retained" or all_lines[idx] == "Upgraded" or all_lines[idx] == "Not Upgraded":
                        temp_lines.append(all_lines[idx])
                        idx += 1
                        break
                    elif all_lines[idx] == "Fresh" and idx + 1 < len(all_lines) and all_lines[idx+1] == "Allotment":
                        temp_lines.append("Fresh Allotment")
                        idx += 2
                        break
                    # Sometimes page numbers interrupt!
                    # If it's a page number, just ignore it?
                    if all_lines[idx].isdigit() and len(all_lines[idx]) < 4:
                        # might be page number
                        pass
                    else:
                        temp_lines.append(all_lines[idx])
                    idx += 1
                
                status = temp_lines[-1] if temp_lines else ""
                cat_lines = temp_lines[:-1]
                
                # Now we need to split cat_lines into Allotted and Candidate category.
                # Usually they are either 1 line each or 2 lines.
                # Let's just join them and split by known categories if possible, or just assume the first half is allotted.
                # Actually, we can look at the previous output.
                # "UR", "OBC-A (Non-", "Creamy Layer)"
                # It's tricky. Let's just output them as one or two fields based on simple heuristics.
                
                if len(cat_lines) == 2:
                    allotted_cat = cat_lines[0]
                    cand_cat = cat_lines[1]
                else:
                    # Just join and store for now, or try to split evenly
                    half = len(cat_lines) // 2
                    allotted_cat = " ".join(cat_lines[:half]) if half > 0 else " ".join(cat_lines)
                    cand_cat = " ".join(cat_lines[half:]) if half > 0 else ""
                    
                    # Better heuristic: Categories are usually from a set: UR, SC, ST, OBC, EWS, etc.
                    # We can just join them and leave it as one string if we can't split cleanly, but CSV is better.
                    # Let's try to reconstruct based on "Layer)" which usually ends OBC.
                    allotted_cat = " ".join(cat_lines)
                    cand_cat = ""
                
                records.append([round_val, rank, choice, institute, course, quota, allotted_cat, cand_cat, status])
            else:
                idx += 1
        except Exception as e:
            print(f"Error at idx {idx}: {e}")
            idx += 1

    with open(csv_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(["Round", "All India Rank", "Choice No.", "Institute", "Course", "Allotted Quota", "Allotted/Candidate Category", "Cand_Cat_Split", "Status"])
        writer.writerows(records)
        
    print(f"Successfully extracted {len(records)} records to {csv_path}")

extract_to_csv('20260324144659106.pdf', 'allotment_result.csv')
