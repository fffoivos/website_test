from transformers import AutoTokenizer
import pandas as pd

dt = pd.read_csv("/home/fivos/Downloads/trapeza_8ematon_nea.csv", header=None)
dt.columns = ['text']

tokenizer = AutoTokenizer.from_pretrained("nlpaueb/bert-base-greek-uncased-v1")

def count_tokens(text, tokenizer=tokenizer):
    if len(tokenizer.tokenize(text)) < 512:
        return True
    else:
        return False

is_length = pd.DataFrame({'under_512' : []})
is_length['under_512'] = dt['text'].apply(count_tokens)

# Convert to DataFrame if needed

dt = pd.DataFrame({
    'text' : dt['text'],
    'under_512' : is_length['under_512']
})

ndx = dt.loc[dt['under_512']==False, 'text'].index
dt = dt.drop(ndx)

print(dt.loc[dt['under_512']==False, 'text'])

dt = dt.drop(columns=['under_512'])
dt['Ποικιλία'] = 1
dt['archaia_or_not'] = 1

dt['Ποικιλία'] = dt['Ποικιλία'].astype(int)
dt['archaia_or_not'] = dt['archaia_or_not'].astype(int)


print(dt.head())

dt.to_csv("/home/fivos/Downloads/trapeza_8ematon_nea2.csv", index=False, encoding='utf-8')
