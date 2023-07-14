from django.shortcuts import render
from django.urls import reverse
from django.http import HttpResponse
import os
from django.conf import settings
import pickle
import re
# pip install --upgrade google-api-python-client
import googleapiclient.discovery
# from googleapiclient.discovery import 
from googletrans import Translator

vectorizer_file = os.path.join(settings.BASE_DIR, 'static', 'vectorizer.pkl')
model_file = os.path.join(settings.BASE_DIR, 'static', 'model.pkl')

# Create your views here.
my_stopwords = ['i', 'me', 'my', 'myself', 'we', 'our', 'ours', 'ourselves', 'you', "you're", "you've", "you'll", "you'd", 'your', 'yours', 'yourself', 'yourselves', 'he', 'him', 'his', 'himself', 'she', "she's", 'her', 'hers', 'herself', 'it', "it's", 'its', 'itself', 'they', 'them', 'their', 'theirs', 'themselves', 'what', 'which', 'who', 'whom', 'this', 'that', "that'll", 'these', 'those', 'am', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'having', 'do', 'does', 'did', 'doing', 'a', 'an', 'the', 'and', 'but', 'if', 'or', 'because', 'as', 'until', 'while', 'of', 'at', 'by', 'for', 'with', 'about', 'between', 'into', 'through', 'during', 'before', 'after', 'above', 'below', 'to', 'from', 'up', 'down', 'in', 'out', 'on', 'over', 'under', 'again', 'further', 'then', 'once', 'here', 'there', 'when', 'where', 'why', 'how', 'all', 'any', 'both', 'each', 'few', 'more', 'most', 'other', 'some', 'such', 'only', 'own', 'same', 'so', 'than', 's', 't', 'can', 'will', 'just', 'don', 'should', "should've", 'now', 'd', 'll', 'm', 'o', 're', 've', 'y', 'ain']

def remove_mystopwords(sentence):
    tokens = sentence.split(" ")
    tokens_filtered= [word for word in tokens if not word in my_stopwords]
    return (" ").join(tokens_filtered)
def fetch_youtube_comments(video_id):
    # Disable OAuthlib's HTTPS verification when running locally.
    # *DO NOT* leave this option enabled in production.
    os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

    api_service_name = "youtube"
    api_version = "v3"
    DEVELOPER_KEY = "AIzaSyA_puXoU8j8zZliEk0kK47TnuTH7DFGLAQ"

    youtube = googleapiclient.discovery.build(api_service_name, api_version, developerKey=DEVELOPER_KEY)

    comments = []
    page_token = None

    while True:
        request = youtube.commentThreads().list(
            part="snippet",
            videoId=video_id,
            maxResults=100,  # Adjust as needed
            pageToken=page_token
        )
        response = request.execute()

        for item in response['items']:
            comment = item['snippet']['topLevelComment']['snippet']['textOriginal']
            comments.append(comment)

        # Check if there are more pages of results
        if 'nextPageToken' in response:
            page_token = response['nextPageToken']
        else:
            break

    return comments
loaded_model=None
cv=None
def load_model():
    global loaded_model, cv
    with open(model_file, 'rb') as f:
      loaded_model=pickle.load(f)
    with open(vectorizer_file, 'rb') as f:
      cv = pickle.load(f)


def predict_sentiment(text):
    text = text.lower()
    text = remove_mystopwords(text)
    cmt = cv.transform([text])
    prediction = loaded_model.predict(cmt)[0]
    return prediction    
    
def sentiment_analysis(request):
    load_model()
    videolink=request.POST.get('videolink')
    VideoId=None
    identifiers =["?v=","&v=","v%3D","/v/","/vi/","/embed/","youtu.be/","/e/"]
    idx=-1
    for i in identifiers:
        idx=videolink.find(i)
        if idx!=-1:
            VideoId=videolink[idx+len(i):idx+len(i)+11]
            break

    comments=fetch_youtube_comments(VideoId)
    negative = 0
    positive = 0
    neutral = 0
    translator = Translator()
    translate=False 
    def Translate(text):
        translated_text = translator.translate(text)
        return translated_text.text

    def cleanTxt(text):
        text = re.sub(r'[^\w]', ' ', str(text))
        return text
    for comment in comments:
        
            comment=cleanTxt(comment)

            if translate==True:
             comment=Translate(comment)
           
            if predict_sentiment(comment) == 1:
#                 print(1,'\n')
                positive += 1
            elif predict_sentiment(comment) == -1:
#                 print(comment,-1,'\n')
                negative += 1
            else:
#                 print(comment,0,'\n')
                neutral += 1
      
    print("positive comments: ", positive)
    print("negative comments: ", negative)
    print("neutral comments: ", neutral)
    percent = (positive)/((positive+negative+neutral))
    percent *= 100
    print("positivity: ", percent,"%")      
    context={
     "positive_comments":positive,
     "negative_comments":negative,
     "neutral_comments":neutral,
     "positivity":percent
    }
    return render(request,'app/results.html',context)          
def index(request):
    print("YES")
    if request.method =='GET':
      re_url=reverse('results')
      return render(request,'app/index.html',context={"re_url":re_url})