import requests
import csv
import time

# --- Configuration ---
# 1. The name of the input file containing a list of ORCID iDs. 
#  Each line should be a single orcid ID (not a url)
INPUT_FILE = "orcid-list.txt"


# 2. Your email address for the OpenAlex polite pool (good practice so they know who is using the api).
YOUR_EMAIL = ""

# 3. Time delay for API
WAIT = 0.25
# ---------------------


def find_and_save_coauthors(orcid_id, email_address):
    """
    Finds all co-authors for a given ORCID iD and saves them to a CSV file.
    """
    print(f"\n{'='*50}\n Processing ORCID iD: {orcid_id}\n{'='*50}")

    # Define the output filename based on the ORCID iD
    output_csv_file = f"co_authors_{orcid_id}.csv"
    
    # This dictionary will store co-author info for the current ORCID
    co_authors = {}

    # Set up the API request parameters
    base_url = "https://api.openalex.org/works"
    params = {
        "filter": f"author.orcid:{orcid_id}",
        "mailto": email_address,
        "per-page": 200,
        "page": 1
    }

    print(f" Fetching works from openalex...")

    # Loop through all pages of results
    while True:
        try:
            response = requests.get(base_url, params=params)
            response.raise_for_status()
            data = response.json()

            works = data.get('results', [])
            if not works:
                break

            for work in works:
                for authorship in work.get('authorships', []):
                    author_info = authorship.get('author', {})
                    
                    raw_primary_orcid = author_info.get('orcid')
                    primary_author_orcid_short = raw_primary_orcid.replace("https://orcid.org/", "") if raw_primary_orcid else ""
                    
                    if primary_author_orcid_short != orcid_id:
                        author_id = author_info.get('id')
                        author_name = author_info.get('display_name')
                        
                        if author_id and author_name:
                            co_author_orcid = author_info.get('orcid') if author_info.get('orcid') else "NA"
                            co_authors[author_id] = {'name': author_name, 'orcid': co_author_orcid}

            print(f"Processed page {params['page']}... Found {len(co_authors)} unique co-authors so far.")
            params['page'] += 1
            time.sleep(WAIT) # Small delay to be polite to the API

        except requests.exceptions.RequestException as e:
            print(f" An API error occurred for {orcid_id}: {e}")
            return # Stop processing this ORCID on error

    # --- Write the final list to a CSV file ---
    if co_authors:
        print(f"\n Writing to CSV file: {output_csv_file} ")
        try:
            sorted_co_authors = sorted(co_authors.items(), key=lambda item: item[1]['name'])

            with open(output_csv_file, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(['openalex_id', 'display_name', 'orcid'])
                for openalex_id, author_data in sorted_co_authors:
                    writer.writerow([openalex_id, author_data['name'], author_data['orcid']])
            
            print(f" Successfully created {output_csv_file} with {len(co_authors)} unique co-authors.")
        except IOError as e:
            print(f" An error occurred while writing the file for {orcid_id}: {e}")
    else:
        print("No co-authors found, so no CSV file was created for this ORCID.")


def main():
    """
    Read ORCIDs from a file and process them.
    """
    try:
        with open(INPUT_FILE, 'r') as f:
            orcid_list = [line.strip() for line in f if line.strip()]
        
        print(f"Found {len(orcid_list)} ORCID iDs in {INPUT_FILE}.")
        
        for orcid in orcid_list:
            find_and_save_coauthors(orcid, YOUR_EMAIL)
            
        print("\n Batch processing complete.")

    except FileNotFoundError:
        print(f" ERROR: The input file '{INPUT_FILE}' was not found.")
        print("Please create this file and add one ORCID iD per line.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")


if __name__ == "__main__":
    main()