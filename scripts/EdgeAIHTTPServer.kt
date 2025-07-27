import android.content.Context
import android.graphics.Bitmap
import android.graphics.BitmapFactory
import android.util.Base64
import com.google.mediapipe.tasks.genai.llminference.LlmInference
import com.google.mediapipe.tasks.genai.llminference.LlmInferenceSession
import com.google.mediapipe.tasks.genai.llminference.LlmInferenceOptions
import com.google.mediapipe.tasks.genai.llminference.LlmInferenceSessionOptions
import com.google.mediapipe.tasks.genai.llminference.GraphOptions
import com.google.mediapipe.framework.image.BitmapImageBuilder
import com.google.mediapipe.framework.image.MPImage
import org.nanohttpd.protocols.http.IHTTPSession
import org.nanohttpd.protocols.http.NanoHTTPD
import org.nanohttpd.protocols.http.response.Response
import org.nanohttpd.protocols.http.response.Status
import org.json.JSONObject

class EdgeAIHTTPServer(private val context: Context) : NanoHTTPD(12345) {

    override fun serve(session: IHTTPSession): Response {
        return try {
            // Health check endpoint
            if (session.method == Method.GET && session.uri == "/health") {
                Response.newFixedLengthResponse(Status.OK, "text/plain", "OK")
            } else if (session.method == Method.POST && session.uri == "/edgeai") {
                // Parse JSON payload
                val body = HashMap<String, String>()
                session.parseBody(body)
                val jsonString = body["postData"] ?: ""
                val json = JSONObject(jsonString)
                val prompt = json.getString("prompt")

                // Run Edge AI model (text only)
                val result = runTextGen(prompt)

                val responseJson = JSONObject()
                responseJson.put("text", result)
                Response.newFixedLengthResponse(Status.OK, "application/json", responseJson.toString())
            } else if (session.method == Method.POST && session.uri == "/edgeai_image") {
                val body = HashMap<String, String>()
                session.parseBody(body)
                val jsonString = body["postData"] ?: ""
                val json = JSONObject(jsonString)
                val prompt = json.getString("prompt")
                val imageBase64 = json.getString("image")

                // Decode base64 image to Bitmap
                val imageBytes = Base64.decode(imageBase64, Base64.DEFAULT)
                val bitmap = BitmapFactory.decodeByteArray(imageBytes, 0, imageBytes.size)

                // Run multimodal inference
                val result = runTextImageGen(prompt, bitmap)

                val responseJson = JSONObject()
                responseJson.put("text", result)
                Response.newFixedLengthResponse(Status.OK, "application/json", responseJson.toString())
            } else {
                Response.newFixedLengthResponse(Status.NOT_FOUND, "text/plain", "Not Found")
            }
        } catch (e: Exception) {
            e.printStackTrace()
            Response.newFixedLengthResponse(Status.INTERNAL_ERROR, "text/plain", "Error: ${e.message}")
        }
    }

    private fun runTextGen(prompt: String): String {
        return try {
            val options = LlmInferenceOptions.builder()
                .setModelPath("gemma3n_e4b_it.task")
                .setMaxTokens(512)
                .build()
            val llmInference = LlmInference.createFromOptions(context, options)
            val sessionOptions = LlmInferenceSessionOptions.builder()
                .setTopK(40)
                .setTemperature(0.8f)
                .build()
            val session = LlmInferenceSession.createFromOptions(llmInference, sessionOptions)
            session.addQueryChunk(prompt)
            val result = session.generateResponse()
            llmInference.close()
            result
        } catch (e: Exception) {
            e.printStackTrace()
            "Error: ${e.message}"
        }
    }

    private fun runTextImageGen(prompt: String, bitmap: Bitmap): String {
        return try {
            val mpImage = BitmapImageBuilder(bitmap).build()
            val options = LlmInferenceOptions.builder()
                .setModelPath("gemma3n_e4b_it.task")
                .setMaxTokens(512)
                .setMaxNumImages(1)
                .build()
            val llmInference = LlmInference.createFromOptions(context, options)
            val sessionOptions = LlmInferenceSessionOptions.builder()
                .setTopK(40)
                .setTemperature(0.8f)
                .setGraphOptions(
                    GraphOptions.builder().setEnableVisionModality(true).build()
                )
                .build()
            val session = LlmInferenceSession.createFromOptions(llmInference, sessionOptions)
            session.addQueryChunk(prompt)
            session.addImage(mpImage)
            val result = session.generateResponse()
            llmInference.close()
            result
        } catch (e: Exception) {
            e.printStackTrace()
            "Error: ${e.message}"
        }
    }
}