import os
import asyncio
from app.agents.background_agent import create_background_agent
from app.agents.main_agent import create_main_agent
from app.agents.onboarding_agent import create_onboarding_agent
from app.models.user import User
from app.services.flow_repository import FlowRepository
from app.schemas.user import UserBase
from app.services.letta_service import get_human_block_id, get_onboarding_agent_id, send_user_message_to_agent
from app.services.user_service import UserRepository
from app.services.whatsapp_service import WhatsAppService

class CreateAgentsFlow:
    FLOW_NAME = "create_agents"

    def __init__(self, user_id: str, data: dict = None):
        self.steps = [self.step_one, self.step_two, self.step_three, self.step_four]
        self.data = data or {}
        self.current_step = 0
        self.is_running = False
        self.flow_completed = None
        self.user_id = user_id
        self.flow_repo = FlowRepository()
        self.user_repo = UserRepository()
        
    async def get_user(self) -> User:
        user_repo = UserRepository()
        user = await user_repo.get_user_by_id(self.user_id)
        if not user:
            raise ValueError(f"User with ID {self.user_id} not found.")
        return user

    async def load_state(self):
        flow_state = await self.flow_repo.get_flow_state(self.FLOW_NAME, self.user_id)
        if flow_state:
            self.current_step = flow_state.get("current_step", 0)
            self.is_running = flow_state.get("is_running", False)
            self.flow_completed = flow_state.get("flow_completed", None)
            self.data = flow_state.get("data", {})
        else:
            await self.save_state()

    async def save_state(self):
        state = {
            "current_step": self.current_step,
            "is_running": self.is_running,
            "flow_completed": self.flow_completed,
            "data": self.data
        }
        await self.flow_repo.set_flow_state(self.FLOW_NAME, self.user_id, state)

    async def start(self, data: dict = None):
        if self.is_running:
            current_step_result = await self.execute_current_step()
            await self.save_state()
            return {
                "message": "Flow is already running.",
                "current_step": current_step_result["message"],
            }
        self.data = data or self.data
        self.current_step = 0
        self.is_running = True
        self.flow_completed = False
        await self.save_state()
        return await self.advance_flow()

    async def advance_flow(self):
        try:
            if self.current_step >= len(self.steps):
                self.is_running = False
                self.flow_completed = True
                await self.save_state()
                return {"message": "Flow completed successfully"}

            current_step_func = self.steps[self.current_step]
            step_result = await current_step_func()
            response = {"message": step_result["message"]}

            if step_result.get("auto_continue"):
                self.current_step += 1
                await self.save_state()
                next_response = await self.advance_flow()
                response["message"] += " " + next_response["message"]
            else:
                response["current_step"] = self.current_step
                self.current_step += 1
                await self.save_state()
            return response
        except Exception as e:
            self.is_running = False
            self.flow_completed = False
            await self.save_state()
            return {"error": f"An error occurred: {str(e)}"}

    async def continue_flow(self):
        if not self.is_running:
            return {"error": "Flow is not running."}
        if self.current_step is None:
            return {"error": "Flow has not been started."}
        return await self.advance_flow()

    async def stop(self):
        if not self.is_running:
            return {"error": "Flow is not running."}
        self.is_running = False
        self.flow_completed = False
        await self.save_state()
        return {"message": "Flow stopped"}

    async def restart(self, data: dict = None):
        self.data = data or self.data
        self.current_step = 0
        self.is_running = True
        self.flow_completed = False
        await self.save_state()
        return await self.advance_flow()

    async def handle_message(self, msg: str):
        msg = msg.lower()
        if msg in ["start", "iniciar"]:
            return await self.start()
        elif msg in ["continue", "ok", "continuar"]:
            return await self.continue_flow()
        elif msg in ["stop", "cancel", "cancelar"]:
            return await self.stop()
        elif msg in ["restart", "reiniciar"]:
            return await self.restart()
        else:
            user = await self.get_user()
            wpp = WhatsAppService(session_name="principal", token=os.getenv("PRINCIPAL_WPP_SESSION_TOKEN"))
            wpp.send_message(user.phone, "Comando inválido. Use 'iniciar', 'continuar', 'cancelar' ou 'reiniciar'.")
            return {"error": "Invalid command. Use 'start', 'continue', 'stop', or 'restart'."}

    async def execute_current_step(self):
        if self.current_step >= len(self.steps):
            return {"message": "No more steps to execute."}
        current_step_func = self.steps[self.current_step]
        return await current_step_func()

####################################################################################################

    async def step_one(self):
        user = await self.get_user()
        
        onboarding_agent = create_onboarding_agent(user_name=user.name, user_number=user.phone)
        human_block_id = get_human_block_id(onboarding_agent.id)
        main_agent = create_main_agent(user_name=user.name, user_number=user.phone, human_block_id=human_block_id)
        create_background_agent(user_name=user.name, user_number=user.phone, human_block_id=human_block_id, main_agent_id=main_agent.id)
        user_main_agent_id_update = UserBase(id_main_agent=main_agent.id)
        await self.user_repo.update_user_by_id(user.id, user_main_agent_id_update)
        
        await asyncio.sleep(1)
        auto_continue = True
        message = f"Step 1 completed"
        return {"message": message, "auto_continue": auto_continue}

    async def step_two(self):
        # user = await self.get_user()
        
        
        await asyncio.sleep(1)  
        auto_continue = True
        message = f"Step 2 completed"
        return {"message": message, "auto_continue": auto_continue}

    async def step_three(self):
        # user = await self.get_user()
        
        
        await asyncio.sleep(1)
        auto_continue = True
        message = f"Step 3 completed"
        return {"message": message, "auto_continue": auto_continue}

    async def step_four(self):
        # user = await self.get_user()
        
        
        message = f"Step 4 completed"
        await asyncio.sleep(1)
        auto_continue = True
        return {"message": message, "auto_continue": auto_continue}
