from supabase import create_client
from config import Config
import json
from datetime import datetime

class Memory:
    def __init__(self):
        if Config.SUPABASE_URL and Config.SUPABASE_KEY:
            self.supabase = create_client(Config.SUPABASE_URL, Config.SUPABASE_KEY)
            self.enabled = True
            # Create table if not exists (you need to create it manually or via migration)
            # Table schema: id, user_id, message, role, timestamp, context
        else:
            self.enabled = False
            print("⚠️ Supabase not configured – memory disabled.")
    
    def store_message(self, user_id, role, content, context=None):
        if not self.enabled:
            return
        try:
            data = {
                "user_id": user_id,
                "role": role,
                "content": content,
                "timestamp": datetime.utcnow().isoformat(),
                "context": json.dumps(context or {})
            }
            self.supabase.table("conversations").insert(data).execute()
        except Exception as e:
            print(f"⚠️ Memory storage failed: {e}")
    
    def get_recent_messages(self, user_id, limit=10):
        if not self.enabled:
            return []
        try:
            resp = self.supabase.table("conversations")\
                .select("*")\
                .eq("user_id", user_id)\
                .order("timestamp", desc=True)\
                .limit(limit)\
                .execute()
            return resp.data[::-1]  # chronological
        except Exception as e:
            print(f"⚠️ Memory retrieval failed: {e}")
            return []
    
    def get_user_preference(self, user_id, key, default=None):
        if not self.enabled:
            return default
        try:
            resp = self.supabase.table("preferences")\
                .select("value")\
                .eq("user_id", user_id)\
                .eq("key", key)\
                .execute()
            if resp.data:
                return resp.data[0]['value']
        except:
            pass
        return default
    
    def set_user_preference(self, user_id, key, value):
        if not self.enabled:
            return
        try:
            # upsert
            existing = self.supabase.table("preferences")\
                .select("id")\
                .eq("user_id", user_id)\
                .eq("key", key)\
                .execute()
            if existing.data:
                self.supabase.table("preferences")\
                    .update({"value": value})\
                    .eq("id", existing.data[0]['id'])\
                    .execute()
            else:
                self.supabase.table("preferences")\
                    .insert({"user_id": user_id, "key": key, "value": value})\
                    .execute()
        except Exception as e:
            print(f"⚠️ Preference save failed: {e}")
