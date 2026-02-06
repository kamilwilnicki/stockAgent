from app.events.agent import StockAgent

class ServiceAgent():

    async def generate_result(self, message):

        agent = StockAgent()
        response = await agent.agent_inference(message)
        return response