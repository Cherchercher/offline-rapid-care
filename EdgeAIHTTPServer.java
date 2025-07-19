// EdgeAIHTTPServer.java
// Reference implementation for Android NanoHTTPD Edge AI bridge with /health endpoint

import android.content.Context;
import com.google.mediapipe.tasks.text.textgen.TextGeneration;

import org.nanohttpd.protocols.http.IHTTPSession;
import org.nanohttpd.protocols.http.NanoHTTPD;
import org.nanohttpd.protocols.http.response.Response;
import org.nanohttpd.protocols.http.response.Status;

import org.json.JSONObject;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;
import java.util.Map;

public class EdgeAIHTTPServer extends NanoHTTPD {

    private Context context;

    public EdgeAIHTTPServer(Context context) {
        super(12345); // Port 12345
        this.context = context;
    }

    @Override
    public Response serve(IHTTPSession session) {
        try {
            // Health check endpoint
            if (session.getMethod() == Method.GET && "/health".equals(session.getUri())) {
                return Response.newFixedLengthResponse(Status.OK, "text/plain", "OK");
            }

            if (session.getMethod() == Method.POST && "/edgeai".equals(session.getUri())) {
                // Parse JSON payload
                Map<String, String> body = new java.util.HashMap<>();
                session.parseBody(body);
                String jsonString = body.get("postData");

                JSONObject json = new JSONObject(jsonString);
                String prompt = json.getString("prompt");

                // Run Edge AI model
                String result = runTextGen(prompt);

                JSONObject responseJson = new JSONObject();
                responseJson.put("text", result);

                return Response.newFixedLengthResponse(Status.OK, "application/json", responseJson.toString());
            }

            return Response.newFixedLengthResponse(Status.NOT_FOUND, "text/plain", "Not Found");

        } catch (Exception e) {
            e.printStackTrace();
            return Response.newFixedLengthResponse(Status.INTERNAL_ERROR, "text/plain", "Error: " + e.getMessage());
        }
    }

    private String runTextGen(String prompt) {
        try {
            InputStream taskStream = context.getAssets().open("gemma3n_e4b_it.task");

            TextGeneration textGen = TextGeneration.createFromFile(context, "gemma3n_e4b_it.task");
            TextGeneration.TextGenerationResult output = textGen.generate(prompt);
            return output.getText();

        } catch (Exception e) {
            e.printStackTrace();
            return "Error: " + e.getMessage();
        }
    }
} 