import unittest
from unittest.mock import patch, MagicMock

# Assuming src is in PYTHONPATH or tests are run from a context where it's discoverable
from service.ai_assistant import AIAssistant
from service.backends import power as power_module # Use alias to avoid conflict with power function if any
from service import common # To mock common.get

class TestAIAssistant(unittest.TestCase):
    def test_get_recommendation_validity(self):
        """
        Tests that AIAssistant.get_recommendation() returns a valid mode.
        """
        assistant = AIAssistant()
        recommendation = assistant.get_recommendation()
        self.assertIn(recommendation, assistant.available_modes,
                      f"Recommendation '{recommendation}' is not in available modes.")

class TestAIOptimizedMode(unittest.TestCase):
    def setUp(self):
        """
        Set up mocks that are common across tests for _ai_optimized.
        """
        # Mock the actual power-setting functions
        self.patcher_performance = patch('service.backends.power._performance', MagicMock(spec=power_module._performance))
        self.patcher_balanced = patch('service.backends.power._balanced', MagicMock(spec=power_module._balanced))
        self.patcher_powersave = patch('service.backends.power._powersave', MagicMock(spec=power_module._powersave))

        self.mock_performance = self.patcher_performance.start()
        self.mock_balanced = self.patcher_balanced.start()
        self.mock_powersave = self.patcher_powersave.start()

        # Mock common.get for configuration
        self.patcher_common_get = patch('service.common.get') # Patching where it's looked up (service.common)
        self.mock_common_get = self.patcher_common_get.start()

        # Mock AIAssistant's get_recommendation method
        self.patcher_ai_get_recommendation = patch('service.ai_assistant.AIAssistant.get_recommendation')
        self.mock_ai_get_recommendation = self.patcher_ai_get_recommendation.start()

        # Mock log to suppress output during tests
        self.patcher_log = patch('service.backends.power.log', MagicMock())
        self.mock_log = self.patcher_log.start()

        # Make sure to stop patches
        self.addCleanup(self.patcher_performance.stop)
        self.addCleanup(self.patcher_balanced.stop)
        self.addCleanup(self.patcher_powersave.stop)
        self.addCleanup(self.patcher_common_get.stop)
        self.addCleanup(self.patcher_ai_get_recommendation.stop)
        self.addCleanup(self.patcher_log.stop)

    def _reset_power_mocks(self):
        self.mock_performance.reset_mock()
        self.mock_balanced.reset_mock()
        self.mock_powersave.reset_mock()

    def test_ai_enabled_recommends_performance(self):
        self._reset_power_mocks()
        self.mock_common_get.side_effect = lambda key, default, section: "true" if key == "enabled" and section == "ai_assistant" else default
        self.mock_ai_get_recommendation.return_value = "performance"

        power_module._ai_optimized()

        self.mock_ai_get_recommendation.assert_called_once()
        self.mock_performance.assert_called_once()
        self.mock_balanced.assert_not_called()
        self.mock_powersave.assert_not_called()

    def test_ai_enabled_recommends_balanced(self):
        self._reset_power_mocks()
        self.mock_common_get.side_effect = lambda key, default, section: "true" if key == "enabled" and section == "ai_assistant" else default
        self.mock_ai_get_recommendation.return_value = "balanced"

        power_module._ai_optimized()

        self.mock_ai_get_recommendation.assert_called_once()
        self.mock_performance.assert_not_called()
        self.mock_balanced.assert_called_once()
        self.mock_powersave.assert_not_called()

    def test_ai_enabled_recommends_powersave(self):
        self._reset_power_mocks()
        self.mock_common_get.side_effect = lambda key, default, section: "true" if key == "enabled" and section == "ai_assistant" else default
        self.mock_ai_get_recommendation.return_value = "powersave"

        power_module._ai_optimized()

        self.mock_ai_get_recommendation.assert_called_once()
        self.mock_performance.assert_not_called()
        self.mock_balanced.assert_not_called()
        self.mock_powersave.assert_called_once()

    def test_ai_enabled_recommends_invalid_falls_back_to_balanced(self):
        self._reset_power_mocks()
        self.mock_common_get.side_effect = lambda key, default, section: "true" if key == "enabled" and section == "ai_assistant" else default
        self.mock_ai_get_recommendation.return_value = "invalid_mode"

        power_module._ai_optimized()

        self.mock_ai_get_recommendation.assert_called_once()
        self.mock_performance.assert_not_called()
        self.mock_balanced.assert_called_once() # Fallback
        self.mock_powersave.assert_not_called()

    def test_ai_disabled_uses_default_mode_performance(self):
        self._reset_power_mocks()
        def config_side_effect(key, default, section):
            if section == "ai_assistant":
                if key == "enabled": return "false"
                if key == "default_mode": return "performance"
            return default
        self.mock_common_get.side_effect = config_side_effect

        power_module._ai_optimized()

        self.mock_ai_get_recommendation.assert_not_called()
        self.mock_performance.assert_called_once()
        self.mock_balanced.assert_not_called()
        self.mock_powersave.assert_not_called()

    def test_ai_disabled_uses_default_mode_balanced(self):
        self._reset_power_mocks()
        def config_side_effect(key, default, section):
            if section == "ai_assistant":
                if key == "enabled": return "false"
                if key == "default_mode": return "balanced"
            return default
        self.mock_common_get.side_effect = config_side_effect

        power_module._ai_optimized()

        self.mock_ai_get_recommendation.assert_not_called()
        self.mock_performance.assert_not_called()
        self.mock_balanced.assert_called_once()
        self.mock_powersave.assert_not_called()

    def test_ai_disabled_uses_default_mode_powersave(self):
        self._reset_power_mocks()
        def config_side_effect(key, default, section):
            if section == "ai_assistant":
                if key == "enabled": return "false"
                if key == "default_mode": return "powersave"
            return default
        self.mock_common_get.side_effect = config_side_effect

        power_module._ai_optimized()

        self.mock_ai_get_recommendation.assert_not_called()
        self.mock_performance.assert_not_called()
        self.mock_balanced.assert_not_called()
        self.mock_powersave.assert_called_once()

    def test_ai_disabled_invalid_default_mode_falls_back_to_balanced(self):
        self._reset_power_mocks()
        def config_side_effect(key, default, section):
            if section == "ai_assistant":
                if key == "enabled": return "false"
                if key == "default_mode": return "invalid_config_mode"
            return default
        self.mock_common_get.side_effect = config_side_effect

        power_module._ai_optimized()

        self.mock_ai_get_recommendation.assert_not_called()
        self.mock_performance.assert_not_called()
        self.mock_balanced.assert_called_once() # Fallback
        self.mock_powersave.assert_not_called()

if __name__ == '__main__':
    unittest.main(verbosity=2)
