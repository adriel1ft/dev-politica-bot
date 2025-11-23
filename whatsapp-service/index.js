import dotenv from "dotenv";
import { WhatsAppClient } from "./client.js";
import { startWebhookServer } from "./webhookServer.js";
import { MessageHandlers } from "./handlers.js"; // Importar a classe

dotenv.config();

const WEBHOOK_PORT = process.env.WEBHOOK_PORT || 3001;
const WHATSAPP_SESSION = process.env.WHATSAPP_SESSION || "default";
const ORCHESTRATOR_URL = process.env.ORCHESTRATOR_URL; // URL do serviço que processará a mensagem

async function main() {
  console.log("[🚀] Iniciando WhatsApp Service...");

  const whatsappClient = new WhatsAppClient({
    sessionName: WHATSAPP_SESSION,
  });

  try {
    await whatsappClient.initialize();
    const client = whatsappClient.getClient();

    // Configurar os handlers para ouvir as mensagens
    const messageHandlers = new MessageHandlers({
      orchestratorUrl: ORCHESTRATOR_URL,
    });
    messageHandlers.setup(client);

    // Iniciar o servidor de webhook para receber comandos de envio
    await startWebhookServer(client, WEBHOOK_PORT);

    console.log("[✨] WhatsApp Service está online e operando.");

  } catch (error) {
    console.error("[❌] Erro fatal ao inicializar o serviço:", error);
    process.exit(1);
  }

  process.on("SIGINT", async () => {
    console.log("\n[🛑] Encerrando WhatsApp Service...");
    await whatsappClient.logout();
    process.exit(0);
  });
}

main();