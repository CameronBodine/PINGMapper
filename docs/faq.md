---
layout: default
title: FAQ's
nav_order: 5
---

# Frequently Asked Questions
{: .no_toc }

If you are having issue's with the software, take a look at the FAQ's. If you cannot find an answer to your question, please submit an [Issue](https://github.com/CameronBodine/PINGMapper/issues). 
{: .fs-6 .fw-300 }

<details open markdown="block">
  <summary>
    Table of contents
  </summary>
  {: .text-delta }
1. TOC
{:toc}
</details>

# Installation

## How do I install PING-Mapper?

See the [installation](./gettingstarted/Installation.md) instructions.

## ModuleNotFoundError

It is possible that `miniconda` or `Anaconda` may not install all the packages required by `PINGMapper`. You will know that this is the case if you recieve a `ModuleNotFoundError` while running the [test script](./gettingstarted/Testing.md). For example, one user recieved the [following error](https://github.com/CameronBodine/PINGMapper/issues/105#issue-2093782805):

```
> Traceback (most recent call last):
>   File "C:\Users\user-name\PINGMapper\test_PINGMapper.py", line 35, in <module>
>     from main_readFiles import read_master_func
>   File "C:\Users\user-name\PINGMapper\src\main_readFiles.py", line 32, in <module>
>     from class_portstarObj import portstarObj
>   File "C:\Users\user-name\PINGMapper\src\class_portstarObj.py", line 31, in <module>
>     from funcs_model import *
>   File "C:\Users\user-name\PINGMapper\src\funcs_model.py", line 42, in <module>
>     from transformers import TFSegformerForSemanticSegmentation
>   File "C:\Users\user-name\.conda\envs\ping\Lib\site-packages\transformers\__init__.py", line 26, in <module>
>     from . import dependency_versions_check
>   File "C:\Users\user-name\.conda\envs\ping\Lib\site-packages\transformers\dependency_versions_check.py", line 16, in <module>
>     from .utils.versions import require_version, require_version_core
>   File "C:\Users\user-name\.conda\envs\ping\Lib\site-packages\transformers\utils\__init__.py", line 32, in <module>
>     from .generic import (
>   File "C:\Users\user-name\.conda\envs\ping\Lib\site-packages\transformers\utils\generic.py", line 432, in <module>
>     import torch.utils._pytree as _torch_pytree
>   File "C:\Users\user-name\AppData\Roaming\Python\Python311\site-packages\torch\__init__.py", line 1504, in <module>
>     from . import masked
>   File "C:\Users\user-name\AppData\Roaming\Python\Python311\site-packages\torch\masked\__init__.py", line 3, in <module>
>     from ._ops import (
>   File "C:\Users\user-name\AppData\Roaming\Python\Python311\site-packages\torch\masked\_ops.py", line 11, in <module>
>     from torch._prims_common import corresponding_real_dtype
>   File "C:\Users\user-name\AppData\Roaming\Python\Python311\site-packages\torch\_prims_common\__init__.py", line 23, in <module>
>     import sympy
> ModuleNotFoundError: No module named 'sympy'
```

The last line of the error states that the `sympy` package was not found. You can attempt to resolve this by manually installing the package with `conda` or `pip`. Using the above as an example, with the `ping` environment activated (run `conda activate ping` in the console), try running the following:

```
conda install sympy
```

If this fails, try installing with `pip`:

```
pip install sympy
```

After successfully installing the missing package, try running the [test](https://cameronbodine.github.io/PINGMapper/docs/gettingstarted/Testing.html). If this does not fix the problem, please submit an [Issue](https://github.com/CameronBodine/PINGMapper/issues).

# Sonar Systems
## What sonar systems does PING-Mapper support?

{: .warning }
> Compatibility with third-party sonar instruments and software does not convey endorsement by PING-Mapper authors.

The software has been designed to work with any Humminbird&reg; side imaging model, but has been specifically tested with the following models:

- 998
- 1198
- 1199
- Helix
- Solix
- Onix

If `PING-Mapper` doesn't work for your Humminbird&reg; recording, submit an [Issue](https://github.com/CameronBodine/PINGMapper/issues).

## What Humminbird&reg; should I purchase?

{: .warning }
> Compatibility with third-party sonar instruments and software does not convey endorsement by PING-Mapper authors.

The software has been designed to work with any Humminbird&reg; side imaging model. We have worked with the Solix, Helix, 1199, and 1198. Humminbird&reg; markets their sonar instruments as "Fish Finders". The name of the fish finder will generally tell you everything you need to know. Let's look at the following example:

**HELIX 12 MSI+ GPS G4N**

**Control Head Model** "HELIX" is the model of the control head. Other models include SOLIX and APEX. The difference between the models, generally speaking, has to do with the bells and whistles available (e.g., bluetooth, WIFI, etc.). This will translate directly to the cost of the system. Please consult the [manufacturer website](https://humminbird.johnsonoutdoors.com) for product-specific information.

If "ICE" is before the model name, then this unit is intended for ice fishing. You don't want these models.

**Screen Size** The control head screen size for example above is "12", or ~12 in. measured across the diagonal. The screen size is up to you and has no impact on the quality of the resulting datasets processed with `PING-Mapper`. Screen size also translates directly to the cost of the system, with larger screen sizes costing more.

**Type of Sonar Supported** "MSI+" is the type of sonar transducers the control head will support. 

The "M" stands for "MEGA" which is the maximum operating frequency of the sonar, e.g., ~1200 kHz. If there is no "M", then "MEGA" frequency is not supported. 

"SI" indicates that this includes a "side imaging" or side-scan transducer (unless there are the letters "CHO" at the end of the name indicating "control head only"). If there is a "DI" instead, then the included transducer is only for "down imaging" and does not support side-scan. 

The "+" indicates more bells and whistles and compatibility including 360 and Live imaging (not currently supported by `PING-Mapper`) and also comes at a higher price-point. You may or may not find the additional features useful for your needs.

Instead of seeing "MSI", it may be spelled out such as "CHIRP SI" or "CHIRP MEGA SI". Again, make sure to get a "side imaging" (SI) sonar. You can opt in or out for MEGA functionality It does provide high resolution images, but at shorter ranges. CHIRP is standard on newer models and helps in resolving (identifying) targets and textures.

**GPS** The presence of "GPS" indicates there is a GPS inside the control head. You can also opt to connect an external Humminbird&reg; heading sensor GPS like [this one](https://humminbird.johnsonoutdoors.com/us/shop/accessories/boat-navigation/ice-as-gps-hs-ice-gps-receiver-heading-sensor). There will also be basemaps available on the control head for viewing while on the water.

**Generation and Networking** Humminbird&reg; has started indicating the model generation of the system. "G4" indicates the fourth generation of this particular unit. The "N" indicates that this model is capable of networking with other Humminbird&reg; models and technology. This may or may not be necessary, depending on your needs.

**Control Head Only** If "CHO" is at the end, then the system you are purchasing does NOT include a sonar transducer. If you want to include a transducer, make sure this is not present.


# Data Collection
## How do I collect high-quality imagery?

See the [data collection](./tutorials/DataCollection.md) tutorial.

## How should I mount the transducer to a vessel?

See the [data collection](./tutorials/DataCollection.md) tutorial.

## What is the minimum depth requirement?

Collecting optimal side-scan imagery requires minimum water depths of ~1 meter. Anything less than this and the sonar intensities are too bright for creating optimal imagery. 

Shallow depths also limits the maximum range, which limits the coverage of a transect. You can think about it from the perspective of looking out of a window on an airplane. When you are on the runway at the airport, you cannot see very far, but you can see a lot of detail. As soon as the plane takes off, you begin to see further, but at decreasing detail as the plane gains altitude. When collecting high quality sonar imagery, it is a balancing act of coverage, which increases with increasing depth, and level of detail, which decreases with increasing depth. In our experience, optimal imagery can be collected at depths of >1 meter to ~20 meters and maximum ranges of 25 to 45 meters. For more information, see the [data collection](./tutorials/DataCollection.md) tutorial.