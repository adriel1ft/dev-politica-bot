import axios from "axios";

export class MessageHandlers {
  constructor(config = {}) {
    // A URL do orquestrador é a única dependência externa necessária.
    this.orchestratorUrl = config.orchestratorUrl;

    if (!this.orchestratorUrl) {
      console.warn("[Aviso] URL do orquestrador não definida. As mensagens recebidas não serão processadas.");
    }
  }

  /**
   * Configura os listeners de eventos no cliente do WhatsApp.
   * @param {wwebjs.Client} whatsappClient - O cliente inicializado do whatsapp-web.js.
   */
  setup(whatsappClient) {
    whatsappClient.on("message", async (msg) => {
      // Ignora mensagens de status ou chamadas
      if (msg.type === 'e2e_notification' || msg.type === 'call_log') {
        return;
      }
      
      try {
        const contact = await msg.getContact();
        const chat = await msg.getChat();

        const payload = {
          messageId: msg.id.id,
          from: msg.from,
          to: msg.to,
          author: msg.author, // Undefined se não for em grupo
          body: msg.body,
          type: msg.type,
          timestamp: msg.timestamp,
          isGroup: chat.isGroup,
          sender: {
            id: contact.id._serialized,
            name: contact.name || contact.pushname,
            shortName: contact.shortName,
            isMe: contact.isMe,
            isUser: contact.isUser,
            isGroup: contact.isGroup,
          }
        };

        // Se for mídia, adiciona a informação para o orquestrador decidir o que fazer
        if (msg.hasMedia) {
            payload.media = {
                mimetype: msg.mimetype,
                filename: msg.filename,
                // O orquestrador pode solicitar o download da mídia via webhook se precisar
            };
        }
        
        console.log(`[📨 Mensagem Recebida] De: ${payload.sender.name} (${payload.sender.id}). Tipo: ${payload.type}.`);
        console.log(`[Mensagem]: ${payload.body}`);
        console.log(payload);
        await this._forwardToOrchestrator(payload);

      } catch (error) {
        console.error("[❌ Erro] Falha ao processar e encaminhar mensagem:", error);
      }
    });

    whatsappClient.on("ready", () => {
      console.log("[✅] Handlers prontos para receber mensagens.");
    });
  }

  /**
   * Encaminha a mensagem recebida para a API orquestradora.
   * @param {object} payload - Os dados da mensagem a serem enviados.
   */
  async _forwardToOrchestrator(payload) {
    if (!this.orchestratorUrl) return;

    try {
      await axios.post(this.orchestratorUrl, payload, {
        timeout: 10000, // 10 segundos de timeout
        headers: { "Content-Type": "application/json" }
      });
      console.log(`[🚀 Encaminhado] Mensagem ${payload.messageId} enviada para o orquestrador.`);
    } catch (error) {
      console.error(`[❌ Webhook] Erro ao enviar para o orquestrador (${this.orchestratorUrl}):`, error.message);
    }
  }
}