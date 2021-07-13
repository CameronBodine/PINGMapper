# PINGMapper
Python interface for reading, processing, and mapping side scan sonar data

## Installation
1. Install [Anaconda](https://www.anaconda.com) or Miniconda (https://docs.conda.io/en/latest/miniconda.html).

2. Open Anaconda Prompt and navigate to where you would like to save PING Mapper.

3. Clone the repo:
```
git clone --depth 1 https://github.com/CameronBodine/PINGMapper
```

4. Create a conda environment called `ping` and activate it:
```
conda env create --file conda/PINGMapper.yml
conda activate ping
```

## Testing PING Mapper
1. Ensure your Anaconda prompt is in the top level of `PINGMapper` directory.

2. Enter the following into the prompt and press enter.  Outputs are found in `.\\PINGMapper\\procData\\PINGMapperTest`.
```
python main.py
```

## Running PING Mapper on your own data
1. Ensure your Anaconda prompt is in the top level of `PINGMapper` directory.

2. Open `main.py` in a text editor/IDE (I use [Atom](https://atom.io/)).

3. Update lines 30-32 with path's to your data and your chosen ouptut directory:
```
humFile = "C:/user/Cam/myHumDat.DAT"
sonPath = "C:/user/Cam/myHumDat"
projDir = "C:/user/Cam/myHumAnswerBox/myHumDat"
```

Windows users: Make sure your filepaths are structured in one of the three following file formats:
- (Double backslashes): `humFile = “C:\\Users\\cam\\Documents\\Programs\\PINGMapper\\Rec00012.DAT”`
- (Path preceded by `r`): `humFile = r“C:\Users\cam\Documents\Programs\PINGMapper\Rec00012.DAT”`
- (Single forward slash): `humFile = “C:/Users/dwhealdo/Documents/Programs/PINGMapper/Rec00012.DAT”`

4. On line 44, update temperature `t=10` with average temperature during scan.

5. On line 46, choose the numper of pings to export per sonar tile.  This can be any value but all testing has been performed on chunk sizes of 500.

6. Run PING Mapper:
```
python main.py
```
