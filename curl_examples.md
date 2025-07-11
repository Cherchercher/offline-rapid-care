# API Endpoint Examples

## Health Check
```bash
curl http://localhost:5001/health
```

## Status Check
```bash
curl http://localhost:5001/status
```

## Text Generation
```bash
curl -X POST http://localhost:5001/chat/text \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [
      {"role": "user", "content": "Hello! Can you tell me a short joke?"}
    ]
  }'
```

## Image Analysis
```bash
curl -X POST http://localhost:5001/chat/image \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [
      {"role": "user", "content": [
        {"type": "image", "url": "./uploads/image_20250707_201615_ChatGPT Image Jul 6, 2025, 04_03_01 PM.png"},
        {"type": "text", "text": "Analyze this image for medical triage assessment."}
      ]}
    ]
  }'
```

## Video Analysis (Placeholder)
```bash
curl -X POST http://localhost:5001/chat/image \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [
      {"role": "user", "content": [
        {"type": "video", "path": "./uploads/coming_out_of_fire.mp4"},
        {"type": "text", "text": "Analyze this video for medical triage assessment."}
      ]}
    ]
  }'
```

## Audio Transcription
```bash
curl -X POST http://localhost:5001/chat/audio \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [
      {"role": "user", "content": [
        {"type": "audio", "audio": "./uploads/audio_f60a5896-f4a4-4eec-97f8-d7f57c396d60_converted.wav"},
        {"type": "text", "text": "Transcribe this audio accurately, preserving medical terminology and patient information."}
      ]}
    ]
  }'
```

## Test Text Endpoint
```bash
curl http://localhost:5001/test-text
```

## Notes

- **Text endpoint**: Uses `text-generation` pipeline for pure text conversations
- **Image endpoint**: Uses `image-text-to-text` pipeline for image analysis
- **Video endpoint**: Currently a placeholder, will use image pipeline on video frames
- **Audio endpoint**: Uses `text-generation` pipeline for audio transcription
- **Images**: Must be embedded in messages using `{"type": "image", "url": "..."}` format
- **Videos**: Must be embedded in messages using `{"type": "video", "path": "..."}` format
- **Audio**: Must be embedded in messages using `{"type": "audio", "audio": "..."}` format
- **Timeout**: 600 seconds (10 minutes) for audio transcription, 300 seconds for image/video analysis, 120 seconds for text 