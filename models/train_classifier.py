import sys
import pandas as pd
from sqlalchemy import create_engine
import nltk
import pickle
from nltk.stem import WordNetLemmatizer
from nltk.corpus import stopwords
from sklearn.pipeline import Pipeline
from sklearn.feature_extraction.text import CountVectorizer, TfidfTransformer
from sklearn.multioutput import MultiOutputClassifier
from sklearn.neighbors import KNeighborsClassifier
from sklearn.model_selection import train_test_split, GridSearchCV

from sklearn.metrics import classification_report
nltk.download(['punkt', 'wordnet', 'stopwords'])


def load_data(database_filepath):
    engine = create_engine(f'sqlite:///{database_filepath}')
    df = pd.read_sql_table("disaster_tweets", engine)
    X = df["message"]
    y = df[[col for col in df.columns if col not in ["id", "message", "original", "genre"]]]
    category_names = [col for col in df.columns if col not in ["id", "message", "original", "genre"]]
    return X, y, category_names


def tokenize(text):
    words = nltk.word_tokenize(text.lower())
    words = [w for w in words if not w in stopwords.words('english')]
    lemmatizer = WordNetLemmatizer()

    clean_tokens = []
    for token in words:
        clean_tok = lemmatizer.lemmatize(token).strip()
        clean_tokens.append(clean_tok)
    return clean_tokens


def build_model():
    pipeline = Pipeline([
        ('vect', CountVectorizer(tokenizer=tokenize)),
        ('tfidf', TfidfTransformer()),
        ("class", MultiOutputClassifier(KNeighborsClassifier()))
    ])
    return pipeline

def fit_model(model, X_train, y_train):
    print('Grid Search for best parameters...')
    parameters = {
        "vect__ngram_range": ((1, 1), (1, 2)),
        # "vect__max_df": (0.5, 1.0),
        # "vect__max_features": (None, 5000, 10000)
    }

    cv = GridSearchCV(model, param_grid=parameters, verbose=3, n_jobs=4)
    cv = cv.fit(X_train, y_train)
    print(cv.best_params_)
    
    return cv.best_estimator_


def evaluate_model(model, X_test, Y_test, category_names):    
    y_preds = cv.predict(X_test)
    df_preds = pd.DataFrame(y_preds, columns=category_names)
    for col in category_names:
        print(classification_report(Y_test[col].values, df_preds[col].values, target_names=[col]))


def save_model(model, model_filepath):
    pickle.dump(model, open(filename, 'wb'))


def main():
    if len(sys.argv) == 3:
        database_filepath, model_filepath = sys.argv[1:]
        print('Loading data...\n    DATABASE: {}'.format(database_filepath))
        X, Y, category_names = load_data(database_filepath)
        X_train, X_test, Y_train, Y_test = train_test_split(X, Y, test_size=0.2)
        
        print('Building model...')
        model = build_model()
        
        print('Training model...')
        model = fit_model(model, X_train, Y_train)
        
        print('Evaluating model...')
        evaluate_model(model, X_test, Y_test, category_names)

        print('Saving model...\n    MODEL: {}'.format(model_filepath))
        save_model(model, model_filepath)

        print('Trained model saved!')

    else:
        print('Please provide the filepath of the disaster messages database '\
              'as the first argument and the filepath of the pickle file to '\
              'save the model to as the second argument. \n\nExample: python '\
              'train_classifier.py ../data/DisasterResponse.db classifier.pkl')


if __name__ == '__main__':
    main()