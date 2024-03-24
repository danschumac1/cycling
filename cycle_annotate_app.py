# -*- coding: utf-8 -*-
"""
Created on Sat Mar 23 21:35:46 2024

@author: dansc
"""

# -*- coding: utf-8 -*-
"""
Created on Mon Mar 4 16:00:12 2024

@author: dansc
"""

# =============================================================================
# IMPORTS
# =============================================================================
import streamlit as st
import pandas as pd
import json

@st.cache_data()
def process_json_to_dataframe(file_path):
    data = []
    all_keys = set()  # To dynamically collect all keys encountered
    
    with open(file_path, 'r') as file:
        for line in file:
            try:
                # Parse the JSON object from each line
                json_obj = json.loads(line)
                data.append(json_obj)
                all_keys.update(json_obj.keys())  # Collect all unique keys
            except json.JSONDecodeError:
                # Skip lines that are not valid JSON
                pass

    # Ensure each dictionary has all keys, filling missing ones with None
    for d in data:
        for key in all_keys:
            if key not in d:
                d[key] = None
    
    # Convert the list of dictionaries to a pandas DataFrame
    df = pd.DataFrame(data)
    return df

# =============================================================================
# LOAD / CLEAN DATA
# =============================================================================
cycle_data = process_json_to_dataframe('./data/all_data_cycling.json').copy()
cycle_data = cycle_data[cycle_data['title'] != ''].copy()  # Use .copy() to ensure 'subs' is not a view but a copy
# cycle_data.loc[:, 'prompt'] = ['TITLE:\n' + t + '\n\nPOST:\n' + st for t, st in zip(cycle_data['title'], cycle_data['selftext'])]
random_sample_1000 = cycle_data.sample(n=1000, random_state=27).reset_index(drop=True)['title']
random_sample_50 = random_sample_1000[0:50]

# Assign splits to annotators


@st.cache_data()
def get_splits_with_mapping(data):
    total_items = len(data) # 1000
    quarter = total_items // 4 # 250
    half = total_items // 2  # 500

    split_indices = {
        "STELLA": list(range(0, quarter)) + list(range(quarter, half)),
        "RIOS": list(range(quarter, half)) + list(range(half, half + quarter)),
        "DAN": list(range(half, half + quarter)) + list(range(half + quarter, total_items)),
        "YOGI": list(range(half + quarter, total_items)) + list(range(0, quarter)),
    }
    
    # Map the split indices to actual data for each annotator, preserving original indexes
    splits = {annotator: data.iloc[indices] for annotator, indices in split_indices.items()}
    
    # Optionally, if you want to reset the index but keep the old index as a column for reference:
    for annotator, df in splits.items():
        splits[annotator] = df.reset_index().rename(columns={'index': 'original_index'})
    
    return splits, split_indices

annotator_splits, annotator_index = get_splits_with_mapping(random_sample_1000)

# =============================================================================
# SAVE AND LOAD FUNCTIONS
# =============================================================================
def save_annotation(annotator_name, original_index, annotator_index, perception_annotation):
    filename = './data/annotations.csv'
    
    try:
        df = pd.read_csv(filename)
    except FileNotFoundError:
        df = pd.DataFrame(columns=['annotator', 'original_index', 'annotator_index', 'perception_annotation'])

    new_row = {'annotator': annotator_name, 'original_index': original_index, 'annotator_index': annotator_index, 'perception_annotation': perception_annotation}
    # Check if the row already exists (based on original_index and annotator_name)
    mask = (df['annotator'] == annotator_name) & (df['original_index'] == original_index)
    if mask.any():
        # Update existing row
        df.loc[mask, ['annotator_index', 'perception_annotation']] = [annotator_index, perception_annotation]
    else:
        # Append new row
        df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
    
    df.to_csv(filename, index=False)

def load_progress_and_find_unannotated(annotator_name):
    filename = f'./data/progress/{annotator_name}_progress.txt'
    try:
        with open(filename, 'r') as f:
            progress = int(f.read())
            return progress
    except FileNotFoundError:
        return 0

def save_progress(annotator_name, index):
    filename = f'./data/progress/{annotator_name}_progress.txt'
    with open(filename, 'w') as f:
        f.write(str(index))

# =============================================================================
# HOME PAGE
# =============================================================================
def show_homepage():
    st.title('Older Adults and ADRD Disorder Annotation App')

    general_guidelines = """
    ## Annotation Guidelines

    Perception of cyclist = based on the headline, does the writer of the headline perceive the cyclist in a positive or negative way. Your rating should be from 1 to 5. 1 represents a complete negative perception of the cyclist. For instance, if the cyclist robbed someone, then the writer probably has a negative perception of the cyclist as is expected. Likewise, if the cyclist saved someone's life, then it should be 5 (a complete positive perception). 3 is neutral, and 2 and 4 are slightly negative and positive perceptions, respectively. There are some examples that are not relevant to cycling at all, in those cases put 0.    
    ***If a comment seems to be borderline, use your best judgment to place it into the correct category. Just make sure that the person being identified as an older adult or suffering from a ADRD disorder is the one receiving the care.***
    """
    
    st.markdown(general_guidelines)
    
    # older_adults_guidelines = """
    # ### Identifying Older Adults Task
    # When identifying older adults, please mark the post if the person receiving care is at or above 65 years old. In the many cases where their age is not explicitly stated, make an inference based on criteria such as whether the individual is a parent or grandparent, whether the conditions they are suffering from are more commonly found in older populations, or any other relevant contextual clues suggesting advanced age. Below are some examples
    # """

    
    # st.markdown(older_adults_guidelines)

    # col1, col2 = st.columns(2)
    
    # with col1:
    #     st.markdown("""
    #     #### Older Adult Related:
    #     - “Grandma had a stroke last night and vomited on the floor” (grandma)
    #     - “My mom has been suffering with dementia for over a decade now” (Mom, decade with dementia)
    #     - “ I was hired to take care of my 95 year old neighbor over the summer” (explicitly mentions age)
    #     - “Any advice for dealing with the abuse that can come from caring for an individual with Alzheimer's?” (Inferred due to Alzheimer’s prevalence in older populations)
    #     """)


    # with col2:
    #     st.markdown("""
    #     #### NOT Older Adult Related:
    #     “When my grandma died, I assumed responsibility taking care of my special needs brother” (The person receiving care is not the grandma)
    #     - “At the ripe age of  67, I am getting too old to be a caregiver” (We cannot make an inference about the person receiving care)
    #     - “He doesn’t have dementia, yet he seems to forget who I am every time I visit” (dementia is negated, no inference should be made)
    #     - "I've been helping my friend recover from surgery by preparing meals and running errands for them" (No mention or inference of elderly individuals)
    #     """)
    
    # ADRD_guidelines = """
    # ### Identifying ADRD
    # When identifying individuals receiving care for Alzheimer’s Disease and Related Dementias (ADRD), please label posts if the care recipient has been diagnosed with an ADRD. This includes common forms like Alzheimer’s Disease, Frontotemporal Dementia (FTD), Lewy Body Dementia (LBD), and Mixed-Etiology Dementias (MED). If a caregiver mentions a diagnosis unfamiliar to you, please search online to determine if it falls under Alzheimer's or dementia. Additionally if a diagnosis is not explicitly stated, but symptoms suggest an ADRD, please mark the post. Such symptoms include memory loss, confusion, disorientation, and misplacing items.
    # """
    
    # st.markdown(ADRD_guidelines)

    
    # col3, col4 = st.columns(2)

    # with col3:
    #     st.markdown("""
    #     #### ADRD-Related:
    #     - “She keeps remembering her abusive spouse fondly but calling me the wrong name” (Inferred based off memory loss)
    #     - “He recently complained about me stealing his keys, then I found out he had placed them in the refrigerator” (Inferred misplacing items, memory)
    #     - “I’ve  been taking care of my older brother with Alzheimer’s Disease for the last few years.” (Explicitly states Alzheimers.)

    #     """)
    
    # with col4:
    #     st.markdown("""
    #     #### Not ADRD Disorder-Related:
    #     - "I've been helping my neighbor with her grocery shopping since she injured her leg" (No mention of ADRD)"
    #     - "She is lucky. Her great grandma had dementia but she just needs help getting around the house (person with cognitive disorder is not the person receiving care)"
    #     - "Our insurance premiums are the lowest they have been in ages! (completely unrelated)"
    #     - "Dr. Alpaca said she has Aphasia and IBS." (After Googling, Aphasia is a cognitive disorder that affects speech expression and understanding but is not considered a ADRD)""
    #     """)



# =============================================================================
# ANNOTATE PAGE FUNCTION WITH FIXED GOTO FUNCTIONALITY
# =============================================================================
def annotate_page(data, annotator_name):
    if 'progress' not in st.session_state or st.session_state['annotator'] != annotator_name:
        st.session_state['progress'] = load_progress_and_find_unannotated(annotator_name)
        st.session_state['annotator'] = annotator_name

    annotator_progress = st.session_state['progress']
    total_questions = len(data)

    st.markdown(f"<h3 style='font-size:24px;'>Question {annotator_progress + 1} of {total_questions}</h3>", unsafe_allow_html=True)

    # Text input to jump to a question
    goto_question = st.text_input("Go to question number:", "")
    if goto_question:
        try:
            goto_index = int(goto_question) - 1
            if 0 <= goto_index < total_questions:
                annotator_progress = goto_index
                st.session_state['progress'] = goto_index
            else:
                st.warning(f"Please enter a number between 1 and {total_questions}.")
        except ValueError:
            st.warning("Enter a valid integer.")
    
    if annotator_progress < total_questions:
        question_data = data.iloc[annotator_progress]
        st.write(f"Text to annotate:\n\n{question_data['title']}")

        # Radio buttons for annotations
        perception_annotation = st.radio("How does the writer of the headline perceive the cyclist? (low = badly, high = positivly, 0 = not relavant)", ('0', '1','2','3','4','5'), key=f"{annotator_progress}_age")

        col1, col2 = st.columns(2)
        if col1.button("Previous"):
            if annotator_progress > 0:
                st.session_state['progress'] -= 1
                st.rerun()

        if col2.button("Next"):
            save_annotation(annotator_name, question_data['original_index'], annotator_progress, perception_annotation)
            save_progress(annotator_name, annotator_progress + 1)
            if annotator_progress + 1 < total_questions:
                st.session_state['progress'] += 1
            else:
                st.session_state['progress'] = 0  # Loop back to the first or handle completion differently
            st.rerun()

    else:
        st.success("You've annotated all assigned texts.")

# =============================================================================
# MAIN APP
# =============================================================================
def main():
    st.sidebar.title("Navigation")
    option = st.sidebar.selectbox('Choose the annotator:', ['Home', "STELLA Annotations", "DAN Annotations", "RIOS Annotations", "YOGI Annotations"])

    if option == 'Home':
        show_homepage()
    else:
        annotator_name = option.split(" ")[0]
        data = annotator_splits[annotator_name]
        annotate_page(data, annotator_name)

# =============================================================================
# RUN THE APP
# =============================================================================
if __name__ == '__main__':
    main()
