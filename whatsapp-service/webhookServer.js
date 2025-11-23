import express from "express";
import wwebjs from "whatsapp-web.js";
const { MessageMedia } = wwebjs;

export function startWebhookServer(whatsappClient, port) {
  const app = express();
  app.use(express.json());

  app.get("/health", (req, res) => {
    res.status(200).json({ status: "ok", isReady: whatsappClient.info != null });
  });

  // Webhook para o orquestrador enviar mensagens
  app.post("/send-message", async (req, res) => {
    const { chatId, message, mediaUrl, mimetype } = req.body;

    if (!chatId || !message) {
      return res.status(400).json({ success: false, error: "Parâmetros 'chatId' e 'message' são obrigatórios." });
    }

    try {
      let media = null;
      if (mediaUrl) {
        console.log(`[📥 Baixando Mídia] de ${mediaUrl}`);
        media = await MessageMedia.fromUrl(mediaUrl, { unsafeMime: mimetype != null });
        if (mimetype) {
            media.mimetype = mimetype;
        }
      }

      console.log(`[📤 Enviando] Para: ${chatId}`);
      const msg = await whatsappClient.sendMessage(chatId, media || message, { caption: media ? message : undefined });
      
      res.status(200).json({ success: true, messageId: msg.id.id });
    } catch (error) {
      console.error("[❌ Erro no Webhook] Falha ao enviar mensagem:", error);
      res.status(500).json({ success: false, error: error.message });
    }
  });

  return new Promise((resolve) => {
    const server = app.listen(port, () => {
      console.log(`[🌐] Servidor Webhook escutando na porta ${port}`);
      resolve(server);
    });
  });
}