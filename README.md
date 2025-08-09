# ComfyGPT


## Quick Start 

### Environment Setup

You can easily set up a environment according to the following command:
```buildoutcfg
conda create -n comfygpt python==3.10
conda activate comfygpt
pip install -r requirements.txt
```

<!-- Additionally, download the `comfy_res` directory from [this link](https://huggingface.co/xiatianzs/comfy_res) and place it in the `./comfygpt/` directory. -->

### Inference
```buildoutcfg
python infer.py --instruction "This workflow can generate image, using sd3 model."
```

