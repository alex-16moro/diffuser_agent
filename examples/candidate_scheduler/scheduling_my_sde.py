# A new engineer's first-cut scheduler, written from memory + an old blog post.
# It "looks" right and may even run on their GPU box — but it breaks the
# diffusers contract in several ways. Run:
#
#   python3 tools/convention_check.py examples/candidate_scheduler
#
# and watch the gate catch each one BEFORE it reaches a reviewer.
import torch
from diffusers.models.unet_2d import UNet2DModel  # DEPR001: moved to models.unets
from diffusers.configuration_utils import ConfigMixin


class MySDEScheduler(ConfigMixin):          # SCHED001: missing SchedulerMixin
    def __init__(self, num_train_timesteps=1000, betas=[]):   # SCHED003 (no @register_to_config), MUT001 (betas=[])
        self.num_train_timesteps = num_train_timesteps
        self.betas = betas

    def step(self, model_output, timestep, sample):   # SCHED002: set_timesteps() is missing
        # REPRO001: torch.randn without a generator -> non-reproducible
        noise = torch.randn(sample.shape)
        # DEVICE001: hardcoded cuda placement
        sample = sample.cuda()
        prev_sample = sample - model_output + noise
        print("stepped", timestep)   # LOG001: print() in library code
        return prev_sample           # (also: should return a SchedulerOutput)
