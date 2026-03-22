# tests/unit/test_simulation.py
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import pytest
from intake.classifier import CaseClassifier
from simulation.courtroom_swarm import CourtroomSwarm


class TestCourtroomSwarm:
    def setup_method(self):
        self.clf   = CaseClassifier()
        self.swarm = CourtroomSwarm(n_agents_per_type=20)

    def test_simulation_returns_result(self):
        case   = self.clf.intake("My landlord evicted me illegally in Karachi Pakistan")
        result = self.swarm.simulate(case, mock=True)
        assert result is not None

    def test_win_probability_between_0_and_1(self):
        case   = self.clf.intake("My employer has not paid wages for 3 months")
        result = self.swarm.simulate(case, mock=True)
        assert 0.0 <= result.overall_win_probability <= 1.0

    def test_arguments_generated(self):
        case   = self.clf.intake("I was wrongfully terminated without notice")
        result = self.swarm.simulate(case, mock=True)
        assert len(result.key_arguments) > 0

    def test_strategy_not_empty(self):
        case   = self.clf.intake("My landlord is harassing me and threatening eviction")
        result = self.swarm.simulate(case, mock=True)
        assert len(result.recommended_strategy) > 10

    def test_arguments_sorted_by_probability(self):
        case   = self.clf.intake("Police arrested me without warrant in the US")
        result = self.swarm.simulate(case, mock=True)
        probs  = [a.favorable_probability for a in result.key_arguments]
        assert probs == sorted(probs, reverse=True)

    def test_deterministic_with_same_input(self):
        case = self.clf.intake("My landlord changed locks in Karachi")
        r1 = self.swarm.simulate(case, mock=True)
        r2 = self.swarm.simulate(case, mock=True)
        assert abs(r1.overall_win_probability - r2.overall_win_probability) < 0.01

    def test_five_agent_types_represented(self):
        case   = self.clf.intake("I was fired without proper procedure")
        result = self.swarm.simulate(case, mock=True)
        if result.key_arguments:
            agent_types = {pos.agent_type for pos in result.key_arguments[0].agent_positions}
            assert len(agent_types) == 5
