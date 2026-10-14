## API Configuration

This project uses Gemini for story generation and review, and Replicate for image generation.

Before running the application, configure your own API credentials in a `.env` file:

- `GEMINI_API_KEY`: Your Gemini API key.
- `REPLICATE_API_TOKEN`: Your Replicate API token.

**Note:** Users must provide their own API credentials and ensure their accounts have sufficient quota or credits. API usage may incur charges.

### Run the application

```bash
python -m pip install -r requirements.txt
python -m pip install streamlit
python -m streamlit run app.py
```

### Offline demo

Select the **Use offline demo** option in the application to test the storybook workflow without making AI API calls. Demo mode uses a sample story and placeholder illustrations.