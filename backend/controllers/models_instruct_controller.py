from typing import List

from backend.services.instruct.compare.models_compare.models_compare import ModelMatcher, ModelRegistryManager


class ModelsInstructorController:

    def get_models_list(self):
        model_manager = ModelRegistryManager()
        data = model_manager.get_available_models()
        return {
            "success": True,
            "data": data,
            "message": ""
        }

    def get_model_comparsion(self, model_key_a, model_key_b, major_name: str,jobs: List ):
        model_matcher = ModelMatcher(model_key_a, model_key_b)
        data = model_matcher.calculate_match_scores(major_name, jobs)
        return{
            "success": True,
            "data": data,
            "message": ""
        }