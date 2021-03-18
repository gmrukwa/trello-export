import base64
import json

import pandas as pd
import streamlit as st
st.set_page_config(layout='wide')


def download_link(object_to_download, download_filename, download_link_text):
    """
    Generates a link to download the given object_to_download.

    object_to_download (str, pd.DataFrame):  The object to be downloaded.
    download_filename (str): filename and extension of file. e.g. mydata.csv, some_txt_output.txt
    download_link_text (str): Text to display for download link.

    Examples:
    download_link(YOUR_DF, 'YOUR_DF.csv', 'Click here to download data!')
    download_link(YOUR_STRING, 'YOUR_STRING.txt', 'Click here to download your text!')

    """
    if isinstance(object_to_download,pd.DataFrame):
        object_to_download = object_to_download.to_csv(index=False)

    # some strings <-> bytes conversions necessary here
    b64 = base64.b64encode(object_to_download.encode()).decode()

    return f'<a href="data:file/txt;base64,{b64}" download="{download_filename}">{download_link_text}</a>'


# data['cards']: list of {'id', 'name', 'closed', 'desc', 'dueReminder', 'idList', 'idLabels', 'dueComplete'}
# data['labels']: list of {'id', 'name', 'board', 'color'}
# data['lists']: list of {'id', 'name', 'closed', 'pos'}
# data['checklists']: list of {'id', 'name', 'idCard', 'pos', 'checkItems'}, 'checkItems': list of {'idChecklist', 'state', 'id', 'name', 'due'}


@st.cache
def load_data(content=None):
    if content is None:
        with open('data/data.json') as infile:
            return json.load(infile)
    else:
        return json.load(content)


@st.cache
def active_lists(content=None):
    data = load_data(content)
    lists = pd.DataFrame(data['lists'])
    lists = lists[~lists['closed']]
    lists.reset_index(inplace=True, drop=True)
    lists = lists[['id', 'name']]
    lists = lists.rename(columns={'id': 'idList', 'name': 'listName'})
    return lists.to_dict('records')


@st.cache
def active_cards(content=None):
    df = pd.DataFrame(load_data(content)['cards'])
    df = df[~df['closed']]
    df = df[['name', 'desc', 'idLabels', 'idList']]
    df.reset_index(inplace=True, drop=True)
    return df


@st.cache
def labels_map(content=None):
    labels = load_data(content)['labels']
    return {l['id']: l['name'] for l in labels}

st.sidebar.header('1. Export your data from Trello')
st.sidebar.write('''
- Show menu
- More
- Print and Export
- Export as JSON
''')
st.sidebar.header('2. Upload file')
trello_content = st.sidebar.file_uploader("Select file", type='json')

if trello_content:
    st.sidebar.header('3. Adjust dump')

    data = load_data(trello_content)
    selected_lists = st.sidebar.multiselect(
        'Lists',
        active_lists(trello_content),
        default=active_lists(trello_content),
        format_func=lambda l: l['listName'],
    )
    selected_labels = st.sidebar.multiselect(
        'Labels',
        data['labels'],
        format_func=lambda l: l['name'],
    )

    st.title('Your cards')

    selected_lists = pd.DataFrame(selected_lists).set_index('idList')
    df = active_cards(trello_content)
    df = df.join(selected_lists, on='idList', how='inner').drop(columns=['idList'])

    df = df[df.idLabels.apply(lambda labels: all(l['id'] in labels for l in selected_labels))]
    df.idLabels = df.idLabels.apply(lambda labels: [labels_map(trello_content)[l] for l in labels])
    df = df.rename(columns={'idLabels': 'labels'})

    st.write(df)

    st.sidebar.header('4. Export')
    tmp_download_link = download_link(df, 'trello.csv', 'Export CSV')
    st.sidebar.markdown(tmp_download_link, unsafe_allow_html=True)
