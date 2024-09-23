# Import các thư viện cần thiết
import os
import joblib
from sklearn.pipeline import Pipeline
from django.conf import settings

# Đường dẫn tới các tệp mô hình đã huấn luyện
model_path = os.path.join(settings.BASE_DIR, 'education_classification_model.pkl')
vectorizer_path = os.path.join(settings.BASE_DIR, 'vectorizer.pkl')
label_encoder_path = os.path.join(settings.BASE_DIR, 'label_encoder.pkl')

# Kiểm tra nếu các tệp tồn tại
if os.path.exists(model_path) and os.path.exists(vectorizer_path) and os.path.exists(label_encoder_path):
    # Load mô hình, vectorizer, và label encoder từ các tệp .pkl đã tải về
    model = joblib.load(model_path)
    vectorizer = joblib.load(vectorizer_path)
    label_encoder = joblib.load(label_encoder_path)
    
    print("Mô hình và các công cụ đã được tải thành công.")
else:
    print("Tệp mô hình không tồn tại. Hãy chắc chắn rằng bạn đã tải về các tệp .pkl từ Google Colab.")
