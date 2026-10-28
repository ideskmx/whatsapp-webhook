
gcloud auth login  

gcloud config set project idesk-store-whatsapp

gcloud run deploy whatsapp-webhook \
  --source . \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars WHATSAPP_VERIFY_TOKEN="AIzaSyDdI0hCZtE6vySjMm-WEfRq3CPzqKqqsHIdNxYhKhm83x1dNL_nm8umimCXkARbteRExWlP12R8WE",GOOGLE_CHAT_WEBHOOK_URL="https://chat.googleapis.com/v1/spaces/AAQAVHFgeyc/messages?key=AIzaSyDdI0hCZtE6vySjMm-WEfRq3CPzqKqqsHI&token=dNxYhKhm83x1dNL_nm8umimCXkARbteRExWlP12R8WE"


