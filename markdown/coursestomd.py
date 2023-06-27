import os
import requests
import json
import sys
from datetime import datetime
from myclass import Collection
from dotenv import dotenv_values


# If True, creates a markdown for every language where we have known words.
# Otherwise set it to false and fill language_codes with the desired languages.
download_all = True
language_codes = ['de']

# If True, it will only make a markdown of shared collections (ignore private)
shared_only = False

# The folder name where we save the markdowns
out_folder = 'all'

############################################################################

# Assumes that .env is on the root
parent_dir = os.path.dirname(os.getcwd())
env_path = os.path.join(parent_dir, '.env')
config = dotenv_values(env_path)

KEY = config["APIKEY"]
headers = {'Authorization': f"Token {KEY}"}

API_URL_V2 = 'https://www.lingq.com/api/v2/'
API_URL_V3 = 'https://www.lingq.com/api/v3/'
API_URL = 'https://www.lingq.com/api/v2/'


def E(myjson):
    json.dump(myjson, sys.stdout, ensure_ascii=False, indent=2)


def get_my_language_codes():
    ''' 
    Returns a list of language codes where I have known words
    '''
    languages = requests.get(
        url=f'{API_URL_V2}languages',
        headers=headers
    ).json()
    codes = [lan['code'] for lan in languages if lan['knownWords'] > 0]

    return codes


def create_README(language_codes):
    '''
    Returns a README markdown:
        * [Greek (el)](./courses/courses_el.md)
        * [English (en)](./courses/courses_en.md)
        * [French (fr)](./courses/courses_fr.md)
        etc.
    '''

    c = open(f'{out_folder}/README.md', 'w', encoding='utf-8')
    for language_code in language_codes:
        c.write(f"* [{language_code}](./courses/courses_{language_code}.md)\n")


def create_markdown(collection_list, language_code):
    out_path = f'{out_folder}/courses/courses_{language_code}.md'
    with open(out_path, 'w', encoding='utf-8') as md:
        # Headings
        fixing_date_width = "&nbsp;" * 6 # Ugly but works
        md.write(f"|Status| |Title|Views|Lessons|Created{fixing_date_width}|Updated{fixing_date_width}|\n")
        md.write(f"|------|-|-----|-----|-------|--------------|--------------|\n")

        for c in collection_list:
            c.viewsCount = "-" if not c.viewsCount else c.viewsCount

            md.write(f"|{c.status}|{c.level}|[{c.title}]({c.course_url})|{c.viewsCount}|{c.amount_lessons}|{c.first_update}|{c.last_update}\n")


def get_shared_collections(language_code):
    '''
    A collection is just a course in the web lingo.
    Given a language code, returns a list of Collection objects. 
    Those store the important information of the JSON to then make the markdown.
    '''

    # API_URL_V3 or API_URL_V2 yield the same here
    my_collections = requests.get(
        url=f"{API_URL_V3}{language_code}/collections/my/", 
        headers=headers
    ).json()
    collection_list = []
    amount_collections = int(my_collections['count'])

    for idx in range(amount_collections):
        # This dictionary is obsolete but it contains the url of the next request
        my_collection = my_collections['results'][idx]

        # WE HAVE TO WORK WITH V2 OF THE API SINCE V3 DOESN'T SUPPORT LESSONS
        # ALTHOUGH WE USE THE STATUS FEATURE FROM V3 SINCE IT DOESN'T EXIST IN V2
        _id = my_collection['id']
        collection_url_v3 = f"https://www.lingq.com/api/v3/{language_code}/collections/{_id}/"
        collection_v3 = requests.get(
            url=collection_url_v3, 
            headers=headers
        ).json()
        # E(collection_v3)

        collection_url_v2 = f"https://www.lingq.com/api/v2/{language_code}/collections/{_id}/"
        collection_v2 = requests.get(
            url=collection_url_v2, 
            headers=headers
        ).json()
        # E(collection_v2)

        col = Collection()
        col.language_code = language_code
        col.status = collection_v3['status']
        col.addData(collection_v2)

        # Ignore private collection if the shared_only flag is true
        if shared_only and col.status != 'shared':
            print(f"  Skipped {col.title} ({idx+1} of {amount_collections})")
            continue
        
        print(f"  Added {col.title} ({idx+1} of {amount_collections})")

        collection_list.append(col)

    return collection_list


def main(language_codes):
    # Create the necessary folders
    if not os.path.exists(out_folder):
        os.mkdir(out_folder)

    courses_path = os.path.join(out_folder, "courses")
    if not os.path.exists(courses_path):
        os.mkdir(courses_path)
    
    # Manage languages to download
    if download_all:
        language_codes = get_my_language_codes()

    create_README(language_codes)

    amount_languages = len(language_codes)
    for idx, language_code in enumerate(language_codes):
        print(f"Starting download for {language_code} ({idx+1} of {amount_languages})")

        collection_list = get_shared_collections(language_code)

        # Sorts by descending date
        collection_list.sort(key=lambda x: datetime.strptime(x.last_update, "%Y-%m-%d"), reverse=True)

        if collection_list:
            create_markdown(collection_list, language_code)
            print(f"Created markdown for {language_code}!")


if __name__ == '__main__':
    main(language_codes)
