# AI Dating App - AI Service

This is the AI microservice component of the AI Dating App ecosystem. It provides AI-powered features like bio generation, matching algorithms, and conversation starters using LangChain and Google Gemini.

## Architecture

This AI service works as a separate microservice that communicates with the frontend:

```
Frontend (React Native) → AI Service (FastAPI)
```

## Features

- **Bio Generation**: Creates personalized dating bios based on user interests
- **AI-Powered Matching**: Analyzes user compatibility (planned)
- **Conversation Starters**: Generates ice-breaker messages (planned)
- **Content Moderation**: AI-powered content filtering (planned)

## Prerequisites

- Python 3.9 or higher
- Google Gemini API key
- Access to the main NestJS backend

## Installation

1. **Clone the repository**

   ```bash
   git clone <repository-url>
   cd ai-dating-app-ai
   ```

2. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**

   ```bash
   # Copy the example environment file
   cp .env.copy .env

   # Edit .env file and add your Google Gemini API key
   # Replace YOUR_GOOGLE_API_KEY_HERE with your actual API key
   ```

4. **Get Google Gemini API Key**
   - Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
   - Create a new API key
   - Copy the key and paste it in your `.env` file

## Running the Service

```bash
# Start the FastAPI server using the new fastapi dev command, this allows FastAPI to listen on all ports
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at: `http://YOUR_IP_ADDRESS:8000`

## API Documentation

Once running, visit:

- **Swagger UI**: `http://127.0.0.1:8000/docs` (recommended)
- **ReDoc**: `http://127.0.0.1:8000/redoc`

## API Endpoints

### POST /bio

Generate personalized dating bios based on user interests.

**Request:**

```json
{
  "bio_interests": ["cooking", "hiking", "photography", "reading"]
}
```

**Response:**

```json
[
  "I love cooking and hiking on weekends. Looking for someone to share adventures with!",
  "Photography and cooking are my passions. Let's explore the world together through food and lens.",
  "Adventure seeker who loves hiking and capturing moments. Ready to create memories with the right person!"
]
```

## Integration with Main Backend

This AI service is designed to be called by the main NestJS backend:

1. **NestJS Backend** receives user requests
2. **Calls AI Service** via HTTP requests
3. **AI Service** processes with LangChain + Gemini
4. **Returns results** to NestJS backend
5. **NestJS** sends response to frontend

### Example NestJS Integration:

```typescript
// In your NestJS service
async generateBio(interests: string[]) {
  const response = await this.httpService.post(
    'http://127.0.0.1:8000/bio',
    { bio_interests: interests }
  ).toPromise();
  return response.data;
}
```

## Environment Variables

Create a `.env` file with the following variables:

```env
GOOGLE_API_KEY=your_google_gemini_api_key_here
LANGSMITH_API_KEY=your_langsmith_key_here  # Optional for tracing (Needed in future)
LANGSMITH_PROJECT=your_project_name        # Optional for tracing (Needed in future)
```

## Development

### Project Structure

```
ai-dating-app-ai/
├── main.py                 # FastAPI application
├── requirements.txt        # Python dependencies
├── .env.copy              # Environment template
├── .env                   # Your environment variables (ignored by git)
├── .gitignore
├── README.md
└── ai/
    └── profile_management/
        ├── ai_profile_management.py  # AI model initialization
        ├── ai_bio_generator.md       # Bio generation prompts
        └── ai_prompt_generator.md    # Other AI prompts
```

### Adding New AI Features

1. Create new prompt files in `ai/profile_management/` or create new folder
2. Add new endpoints in `main.py`
3. Update this README with new API documentation

## Troubleshooting

### Common Issues

1. **API key errors**: Verify your Google Gemini API key is correct
2. **Port conflicts**: Change the port in the uvicorn command if 8000 is taken

### Logs

The service uses LangSmith for tracing. Check your LangSmith dashboard for detailed AI interaction logs.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is part of the AI Dating App ecosystem.
