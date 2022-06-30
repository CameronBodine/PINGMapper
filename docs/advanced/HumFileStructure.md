---
layout: default
title: Humminbird File Structure
nav_order: 1
parent: Advanced Topics

nav_exclude: false
---


# Humminbird&reg; File Structure

## Introduction
`PING-Mapper` is a new and optimized version of `PyHum` [[1]](#1) [[2]](#2). Since the release of `PyHum`, additional and enhanced functionality has been identified by the software authors and end-users, including Python 3 compatibility.  This can only be achieved with a complete understanding of the Humminbird&reg; recording file structure.  This report documents new findings on the file structure of Humminbird&reg; sonar recordings, essential for processing and exporting raw sonar data.

## SD Card Files

Sonar recordings from Humminbird&reg; side imaging sonar systems are saved to a SD card inserted into the control head. Each sonar recording consists of a `DAT` file and commonly named subdirectory containing `SON` and `IDX` files.  The directory of saved recordings have the following structure:

```
Rec00001.DAT
├── Rec00001
│   ├── B001.IDX
│   ├── B001.SON
│   ├── B002.IDX
│   ├── B002.SON
│   ├── B003.IDX
│   ├── B003.SON
│   ├── B004.IDX
│   └── B004.IDX
Rec00002.DAT
├── Rec00002
│   ├── B001.IDX
│   ├── B001.SON
│   ├── B002.IDX
│   ├── B002.SON
│   ├── B003.IDX
│   ├── B003.SON
│   ├── B004.IDX
│   └── B004.IDX
....
```

## DAT File Structure
The `DAT` file contains metadata that applies to the sonar recording.  It includes information related water type specified on the sonar unit, the Unix date and time when the sonar recording began, geographic location where the recording began, name of the recording, number of sonar records, and length of the recording.  The size (in bytes) of the `DAT` file varies by Humminbird&reg; model (and potentially firmware).  The following sections indicate the offset from start of the `DAT` file and description of the data for each model.


### 9xx/ 11xx/ Helix/ Solix Series

The `DAT` file structure is the same for the 9xx, 11xx, Helix, and Solix series models.

**TABLE: DAT Structure**

| Name              | Offset (9xx, 11xx, Helix) | Offset (Solix) | Description |
| ----------------- | ------------------------- | -------------- | ----------- |
| DAT Beginning     | +0                        | +0             | Beginning of DAT File |
| Water Type        | +1                        | +1             | 0='fresh' (freshwater); 1='deep salt'; 2='shallow salt'; otherwise='unknown' |
| -                 | +2-3                      | +2-3           | -           |
| Firmware Version (?) | +4                     | +4             | Installed firmware version (?) |
| -                 | +8-19                     | +8-19          | -           |
| Unix Date/Time    | +20                       | +20            | Recording start date and time |
| UTM X             | +24                       | +24            | EPSG 3395 Easting |
| UTM Y             | +28                       | +28            | EPSG 3395 Northing |
| Recording Name    | +32                       | +32            | Recording name |
| -                 | +42-43                    | +42-43         | Unknown     |
| Number of Records | +44                       | +44            | Number of pings |
| Length            | +48                       | +48            | Length (in milliseconds) of sonar recording |
| -                 | +52-59                    | +52-91         | -           |
| DAT End           | +60                       | +92            | End of DAT File |



### Onix Series
The Onix series has a different structure from other Humminbird&reg; models.  The first 24 bytes are in binary containing information about water type, number of pings in the recording, total time of recording, and ping size in bytes.  Following the binary header are ascii strings (human readable) containing additional information, with each piece of information encapsulated with `<attribute=value>`.

**TABLE: Binary Header**

| Name              | Offset | Description |
| ----------------- | ------ | ----------- |
| DAT Beginning     | +0     | Beginning of DAT File |
| Water Type        | +1     | 0='fresh' (freshwater); 1='deep salt'; 2='shallow salt'; otherwise='unknown' |
| Unknown           | +2-3   | -           |
| Number of Pings   | +4     | Number of sonar records/pings |
| Length            | +8     | Length (in milliseconds) of sonar recording |
| Ping Size (Bytes) | +12    | Number of returns per ping |
| First Ping Period | +16    | First ping period (in milliseconds) |
| Beam Mask         | +20    | Unknown     |
| Spacer            | +24    | Spacer preceding ascii text |

**TABLE: Ascii Text**

| Name              | Example              |
| ----------------- | ---------------------- |
| Version           | < Version=SonarRecordThumbVersion > |
| Number of Pings   | < NumberOfPings=11712 > |
| Total Time Ms     | < TotalTimeMs=143092 > |
| Ping Size Bytes   | < PingSizeBytes=1652 > |
| First Ping Period | < FirstPingPeriodMs=1 > |
| Beam Mask         | < BeamMask=30 > |
| Chirp 1 Start Freq | < Chirp1StartFrequency=0 > |
| Chirp 1 End Freq  | < Chirp1EndFrequency=0 > |
| Chirp 2 Start Freq | < Chirp2StartFrequency=0 > |
| Chirp 2 End Freq  | < Chirp2EndFrequency=0 > |
| Chirp 3 Start Freq | < Chirp3StartFrequency=0 > |
| Chirp 3 End Freq  | < Chirp3EndFrequency=0 > |
| Source Device Model ID 2D | < SourceDeviceModelId2D=1001 > |
| Source Device Model ID SI | < SourceDeviceModelIdSI=1001 > |
| Source Device Model ID DI | < SourceDeviceModelIdDI=1001 > |


## IDX and SON File Structure
A `SON` file contains every sonar ping for a specific sonar channel (see table below) while the `IDX` file stores the byte offset and time ellapsed for each sonar ping. The `IDX` file allows quick navigation to locate pings in the `SON` file but can become corrupt due to power failure during the survey. Decoding the `SON` file without the `IDX` file requires additional information, outlined in the sections below.

**TABLE: Sonar Channel File Names**

| File Name | Description                 | Frequency         |
| --------- | --------------------------- | ----------------- |
| B000.SON  | Down Scan Low Frequency     | 50/83 kHz         |
| B001.SON  | Down Scan High Frequency    | 200 kHz           |
| B002.SON  | Side Scan Port              | 455/800/1,200 kHz |
| B003.SON  | Side Scan Starboard         | 455/800/1,200 kHz |
| B004.SON  | Down Scan MEGA Frequency    | 1,200 kHz         |

Each `SON` file contains all the pings (ping header and returns) that were recorded.  Each ping begins with a header, containing metadata specific to that ping (see [Header Structure](#header-structure) below).  The header is followed by 8-bit (0-255 Integer) values representing the returns for that ping.  All data stored in `SON` files are signed integer big endian.

### Ping Structure
The number of bytes for a ping varies in two ways.  First, the number of bytes corresponding to ping attributes vary by model (and potentially firmware version), resulting in varying header length.  Second, the number of ping returns vary depending on the range set while recording the sonar.  The variability in the size of a ping across recordings and Humminbird&reg; models make automatic decoding of the file a non-trivial task.  Consistent structure between recordings and Humminbird&reg; models, however, has been identified.  

Each ping begins with the same four hexidecimal values: `C0 DE AB 21`.  This sequence is common to all sonar recordings encountered to date.  The header then terminates with the following hexidecimal sequence: `A0 ** ** ** ** 21` where the `** ** ** **` is a 32-byte unsigned integer indicating the number of sonar returns that are recorded immediately after `21`.  By counting the number of bytes beginning at `C0` and terminating at `21`, the correct header length can be determined.  Three different header lengths have been identified:

**TABLE: Header Length by Model**

| Header Length | Humminbird Model |
| ------------- | ---------------- |
| 67 Bytes      | 9xx              |
| 72 Bytes      | 11xx, Helix, Onix|
| 152 Bytes     | Solix            |

#### Header Structure
The header for a ping contains attributes specific to that ping.  Information about the ping location, time elapsed since beginning of the recording, heading, speed, depth, etc. are contained in this structure.  The attribute is preceded by a hexidecimal value that is unique for the data that follows, referred to as a tag.  For example, `Depth` is tagged by a hexidecimal value of `87`.  While the variety of information stored in the header varies by Humminbird&reg; model, tags consistently identify the type of information that follows.  The following sections indicate the tags, the attribute that follows the tag, and byte offset for the attribute by model.

**TABLE: Ping Header Structure**

| Name              | Description               | Hex Tag | 9xx     | 11xx, Helix, Onix | Solix |
| ----------------- | ------------------------- | ------- | ------- | ----------------- | ----- |
| Ping #1           | Beginning of ping         | `C0`    | +0      | +0                | +0    |
| Header Start      | Beginning of ping header  | `21`    | +3      | +3                | +3    |
| Record Number     | Unique ping ID            | `80`    | +5      | +5                | +5    |
| Time Elapsed      | Time elapsed (msec)       | `81`    | +10     | +10               | +10   |
| UTM X             | EPSG 3395 easting coord.  | `82`    | +15     | +15               | +15   |
| UTM Y             | EPSG 3395 northing coord. | `83`    | +20     | +20               | +20   |
| Heading Quality   | Quality flag[^a]          | `84`    | +25     | +25               | +25   |
| Heading           | Vessel heading (1/10 deg) | -       | +27     | +27               | +27   |
| Speed Quality     | Quality flag[^a]          | `85`    | +30     | +30               | +30   |
| Speed             | Vessel speed (cm/sec)     | -       | +32     | +32               | +32   |
| *NA*              | Unknown data contents     | `86`    | -       | +35               | +35   |
| Depth             | Sonar depth (cm)          | `87`    | +35     | +40               | +40   |
| *NA*              | Unknown data contents     | -       | -       | -                 | +44-83 |
| Sonar Beam        | Sonar beam ID[^b]         | `50`    | +40     | +45               | +85   |
| Voltage Scale     | Voltage scale (1/10 volt) | `51`    | +42     | +47               | +87   |
| Frequency         | Sonar beam frequency (Hz) | `92`    | +44     | +49               | +89   |
| *NA*              | Unknown data contents     | -       | +48-60  | +53-65            | +89-145 |
| Return Count      | Number ping returns (*n*) | `A0`    | +62     | +67               | +147  |
| Header End        | End of ping header        | `21`    | +66     | +72               | +152  |
| Ping Returns      | Sonar intensity [0-255]   | `21`    | +67     | +73               | +152  |
| Ping #2           | Beginning of ping         | `C0`    | +67+*n*+1 | +73+*n*+1       | +152+*n*+1 |
| ...[^c]           | ...                       | ...     | ...     | ...               | ...   |


[^a]: 0=bad; 1=good.
[^b]: See [Sonar Channel File Names](#idx-and-son-file-structure) table for frequency values.
[^c]: Pattern repeats for duration of sonar recording.



## References

<a id="1">[1]</a> Buscombe, D., Grams, P. E., & Smith, S. M. C. (2015). Automated Riverbed Sediment Classification Using Low-Cost Sidescan Sonar. Journal of Hydraulic Engineering, 142(2), 06015019. https://doi.org/10.1061/(ASCE)HY.1943-7900.0001079

<a id="2">[2]</a> Buscombe, D. (2017). Shallow water benthic imaging and substrate characterization using recreational-grade sidescan-sonar. Environmental Modelling and Software, 89, 1–18. https://doi.org/10.1016/j.envsoft.2016.12.003





<!-- ##### 2.2.1.2) Humminbird&reg; 900 Series
Header Length (Bytes): **67**

| Name              | Offset | Length | Bytes | Hex Value     | Integer Value | Description |
| ----------------- | ------ | ------ | ----- | ------------- | ------------- | ----------- |
| Header Start      | +0     | 4      | 32    | `A0 DE AB 21` | 3235818273    | Beginning of ping |
| Tag 80            | +4     | 1      | 8     | `80`          | 128           | - |
| **Record Number** | +5     | 4      | 32    | *Varies*      | *Varies*      | Unique ping ID |
| Tag 81            | +9     | 1      | 8     | `81`          | 129           | - |
| **Time Elapsed**  | +10    | 4      | 32    | *Varies*      | *Varies*      | Time elapsed (in milliseconds) |
| Tag 82            | +14    | 1      | 8     | `82`          | 130           | - |
| **UTM X**         | +15    | 4      | 32    | *Varies*      | *Varies*      | EPSG 3395 Easting |
| Tag 83            | +19    | 1      | 8     | `83`          | 131           | - |
| **UTM Y**         | +20    | 4      | 32    | *Varies*      | *Varies*      | EPSG 3395 Northing |
| Tag 84            | +24    | 1      | 8     | `84`          | 132           | - |
| **GPS Flag (?)**  | +25    | 2      | 16    | *Varies*      | *Varies*      | Quality flag for heading (?) 0=bad; 1=good |
| **Heading**       | +27    | 2      | 16    | *Varies*      | *Varies*      | Heading in tenths of a degree |
| Tag 85            | +29    | 1      | 8     | `85`          | 133           | - |
| **GPS Flag (?)**  | +30    | 2      | 16    | *Varies*      | *Varies*      | Quality flag for speed (?) 0=bad; 1=good |
| **Speed**         | +32    | 2      | 16    | *Varies*      | *Varies*      | Vessel speed in centimeters/second|
| Tag 87            | +34    | 1      | 8     | `87`          | 135           | - |
| **Depth**         | +35    | 4      | 32    | *Varies*      | *Varies*      | Sensor depth in centimeters |
| Tag 50            | +39    | 1      | 8     | `50`          | 80            | - |
| **Sonar Beam**    | +40    | 1      | 8     | *Varies*      | *Varies*      | 0=DS Low Freq; 1=DS High Freq; 2=SS Port; 3=SS Star |
| Tag 51            | +41    | 1      | 8     | `51`          | 81            | - |
| **Volt Scale**    | +42    | 1      | 8     | *Varies*      | *Varies*      | Voltage in tenths |
| Tag 92            | +43    | 1      | 8     | `92`          | 146           | - |
| **Frequency**     | +44    | 4      | 32    | *Varies*      | *Varies*      | Frequency in hertz |
| Tag 53            | +48    | 1      | 8     | `53`          | 83            | - |
| **Unknown**       | +49    | 1      | 8     | *Varies*      | *Varies*      | Unknown |
| Tag 54            | +50    | 1      | 8     | `54`          | 84            | - |
| **Unknown**       | +51    | 1      | 8     | *Varies*      | *Varies*      | Unknown |
| Tag 95            | +52    | 1      | 8     | `149`         | 149           | - |
| **Unknown**       | +53    | 4      | 32    | `00 00 00 1A` | 26            | Unknown |
| Tag 56            | +57    | 1      | 8     | `56`          | 86            | - |
| **+- UTM X (?)**  | +58    | 1      | 8     | *Varies*      | *Varies*      | Possibly +- UTM X in centimeters |
| Tag 57            | +59    | 1      | 8     | `57`          | 87            | - |
| **+- UTM Y (?)**  | +60    | 1      | 8     | *Varies*      | *Varies*      | Possibly +- UTM Y in centimeters |
| Tag A0            | +61    | 1      | 8     | `A0`          | 160           | - |
| **Bytes in Ping** | +62    | 4      | 32    | *Varies*      | *Varies*      | Number of bytes in ping returns |
| End Header        | +66    | 1      | 8     | `21`          | 33            | End of ping header |


##### 2.2.1.3) Humminbird&reg; 1100 & Helix Series
Header Length (Bytes): **72**  
*Note:* The structure is the same as 900 series for offset 0 - 33.

| Name              | Offset | Length | Bytes | Hex Value     | Integer Value | Description |
| ----------------- | ------ | ------ | ----- | ------------- | ------------- | ----------- |
| Header Start      | +0     | 4      | 32    | `A0 DE AB 21` | 3235818273    | Beginning of ping |
| Tag 80            | +4     | 1      | 8     | `80`          | 128           | - |
| **Record Number** | +5     | 4      | 32    | *Varies*      | *Varies*      | Unique ping ID |
| Tag 81            | +9     | 1      | 8     | `81`          | 129           | - |
| **Time Elapsed**  | +10    | 4      | 32    | *Varies*      | *Varies*      | Time elapsed (in milliseconds) |
| Tag 82            | +14    | 1      | 8     | `82`          | 130           | - |
| **UTM X**         | +15    | 4      | 32    | *Varies*      | *Varies*      | EPSG 3395 Easting |
| Tag 83            | +19    | 1      | 8     | `83`          | 131           | - |
| **UTM Y**         | +20    | 4      | 32    | *Varies*      | *Varies*      | EPSG 3395 Northing |
| Tag 84            | +24    | 1      | 8     | `84`          | 132           | - |
| **GPS Flag (?)**  | +25    | 2      | 16    | *Varies*      | *Varies*      | Quality flag for heading (?) 0=bad; 1=good |
| **Heading**       | +27    | 2      | 16    | *Varies*      | *Varies*      | Heading in tenths of a degree |
| Tag 85            | +29    | 1      | 8     | `85`          | 133           | - |
| **GPS Flag (?)**  | +30    | 2      | 16    | *Varies*      | *Varies*      | Quality flag for speed (?) 0=bad; 1=good |
| **Speed**         | +32    | 2      | 16    | *Varies*      | *Varies*      | Vessel speed in centimeters/second|
| Tag 86            | +34    | 1      | 8     | `86`          | 134           | - |
| **Unknown**       | +35    | 4      | 32    | `00 00 00 00` | 0             | Unknown |
| Tag 87            | +39    | 1      | 8     | `87`          | 135           | - |
| **Depth**         | +40    | 4      | 32    | *Varies*      | *Varies*      | Sensor depth in centimeters |
| Tag 50            | +44    | 1      | 8     | `50`          | 80            | - |
| **Sonar Beam**    | +45    | 1      | 8     | *Varies*      | *Varies*      | 0=DS Low Freq; 1=DS High Freq; 2=SS Port; 3=SS Star; 4=DS MEGA (if present) |
| Tag 51            | +46    | 1      | 8     | `51`          | 81            | - |
| **Volt Scale**    | +47    | 1      | 8     | *Varies*      | *Varies*      | Voltage in tenths |
| Tag 92            | +48    | 1      | 8     | `92`          | 146           | - |
| **Frequency**     | +49    | 4      | 32    | *Varies*      | *Varies*      | Frequency in hertz |
| Tag 53            | +53    | 1      | 8     | `53`          | 83            | - |
| **Unknown**       | +54    | 1      | 8     | *Varies*      | *Varies*      | Unknown |
| Tag 54            | +55    | 1      | 8     | `54`          | 84            | - |
| **Unknown**       | +56    | 1      | 8     | *Varies*      | *Varies*      | Unknown |
| Tag 95            | +57    | 1      | 8     | `95`          | 149           | - |
| **Unknown**       | +58    | 4      | 32    | `00 00 00 1A` | 26            | Unknown |
| Tag 56            | +62    | 1      | 8     | `56`          | 86            | - |
| **+- UTM X (?)**  | +63    | 1      | 8     | *Varies*      | *Varies*      | Possibly +- UTM X in centimeters |
| Tag 57            | +64    | 1      | 8     | `57`          | 87            | - |
| **+- UTM Y (?)**  | +65    | 1      | 8     | *Varies*      | *Varies*      | Possibly +- UTM Y in centimeters |
| Tag A0            | +66    | 1      | 8     | `A0`          | 160           | - |
| **Bytes in Ping** | +67    | 4      | 32    | *Varies*      | *Varies*      | Number of bytes in ping returns |
| End Header        | +71    | 1      | 8     | `21`          | 33            | End of ping header |


##### 2.2.1.4) Humminbird&reg; Solix Series
Header Length (Bytes): **152**  
*Note:* The structure is the same as 1100/Helix series for offset 0 - 43.

| Name              | Offset | Length | Bytes | Hex Value     | Integer Value | Description |
| ----------------- | ------ | ------ | ----- | ------------- | ------------- | ----------- |
| Head Start        | +0     | 4      | 32    | `A0 DE AB 21` | 3235818273    | Beginning of ping |
| Tag 80            | +4     | 1      | 8     | `80`          | 128           | - |
| **Record Number** | +5     | 4      | 32    | *Varies*      | *Varies*      | Unique ping ID |
| Tag 81            | +9     | 1      | 8     | `81`          | 129           | - |
| **Time Elapsed**  | +10    | 4      | 32    | *Varies*      | *Varies*      | Time elapsed (in milliseconds) |
| Tag 82            | +14    | 1      | 8     | `82`          | 130           | - |
| **UTM X**         | +15    | 4      | 32    | *Varies*      | *Varies*      | EPSG 3395 Easting |
| Tag 83            | +19    | 1      | 8     | `83`          | 131           | - |
| **UTM Y**         | +20    | 4      | 32    | *Varies*      | *Varies*      | EPSG 3395 Northing |
| Tag 84            | +24    | 1      | 8     | `84`          | 132           | - |
| **GPS Flag (?)**  | +25    | 2      | 16    | *Varies*      | *Varies*      | Quality flag for heading (?) 0=bad; 1=good |
| **Heading**       | +27    | 2      | 16    | *Varies*      | *Varies*      | Heading in tenths of a degree |
| Tag 85            | +29    | 1      | 8     | `85`          | 133           | - |
| **GPS Flag (?)**  | +30    | 2      | 16    | *Varies*      | *Varies*      | Quality flag for speed (?) 0=bad; 1=good |
| **Speed**         | +32    | 2      | 16    | *Varies*      | *Varies*      | Vessel speed in centimeters/second|
| Tag 86            | +34    | 1      | 8     | `86`          | 134           | - |
| **Unknown**       | +35    | 4      | 32    | `00 00 00 00` | 0             | Unknown |
| Tag 87            | +39    | 1      | 8     | `87`          | 135           | - |
| **Depth**         | +40    | 4      | 32    | *Varies*      | *Varies*      | Sensor depth in centimeters |
| Tag 88            | +44    | 1      | 8     | `88`          | 136           | - |
| **Unknown**       | +45    | 4      | 32    | `A1 B2 C3 D4` | 2712847316    | Unknown |
| Tag 89            | +49    | 1      | 8     | `89`          | 137           | - |
| **Unknown**       | +50    | 4      | 32    | `A1 B2 C3 D4` | 2712847316    | Unknown |
| Tag 8A            | +54    | 1      | 8     | `8A`          | 138           | - |
| **Unknown**       | +55    | 4      | 32    | `A1 B2 C3 D4` | 2712847316    | Unknown |
| Tag 8B            | +59    | 1      | 8     | `8B`          | 139           | - |
| **Unknown**       | +60    | 4      | 32    | `A1 B2 C3 D4` | 2712847316    | Unknown |
| Tag 8C            | +64    | 1      | 8     | `8C`          | 140           | - |
| **Unknown**       | +65    | 4      | 32    | `A1 B2 C3 D4` | 2712847316    | Unknown |
| Tag 8D            | +69    | 1      | 8     | `8D`          | 141           | - |
| **Unknown**       | +70    | 4      | 32    | `A1 B2 C3 D4` | 2712847316    | Unknown |
| Tag 8E            | +74    | 1      | 8     | `8E`          | 142           | - |
| **Unknown**       | +75    | 4      | 32    | `A1 B2 C3 D4` | 2712847316    | Unknown |
| Tag 8F            | +79    | 1      | 8     | `8F`          | 143           | - |
| **Unknown**       | +80    | 4      | 32    | `A1 B2 C3 D4` | 2712847316    | Unknown |
| Tag 50            | +84    | 1      | 8     | `50`          | 80            | - |
| **Sonar Beam**    | +85    | 1      | 8     | *Varies*      | *Varies*      | 0=DS Low Freq; 1=DS High Freq; 2=SS Port; 3=SS Star; 4=DS MEGA |
| Tag 51            | +86    | 1      | 8     | `51`          | 81            | - |
| **Volt Scale**    | +87    | 1      | 8     | *Varies*      | *Varies*      | Voltage in tenths |
| Tag 92            | +88    | 1      | 8     | `92`          | 146           | - |
| **Frequency**     | +89    | 4      | 32    | *Varies*      | *Varies*      | Frequency in hertz |
| Tag 53            | +93    | 1      | 8     | `53`          | 83            | - |
| **Unknown**       | +94    | 1      | 8     | *Varies*      | *Varies*      | Unknown |
| Tag 54            | +95    | 1      | 8     | `54`          | 84            | - |
| **Unknown**       | +96    | 1      | 8     | *Varies*      | *Varies*      | Unknown |
| Tag 95            | +97    | 1      | 8     | `95`          | 149           | - |
| **Unknown**       | +98    | 4      | 32    | `00 00 00 1A` | 26            | Unknown |
| Tag 56            | +102   | 1      | 8     | `56`          | 86            | - |
| **+- UTM X (?)**  | +103   | 1      | 8     | *Varies*      | *Varies*      | Possibly +- UTM X in centimeters |
| Tag 57            | +104   | 1      | 8     | `57`          | 87            | - |
| **+- UTM Y (?)**  | +105   | 1      | 8     | *Varies*      | *Varies*      | Possibly +- UTM Y in centimeters |
| Tag 98            | +106   | 1      | 8     | `98`          | 152           | - |
| **Unknown**       | +107   | 4      | 32    | `00 00 00 04` | 4             | Unknown |
| Tag 99            | +111   | 1      | 8     | `99`          | 153           | - |
| **Unknown**       | +112   | 4      | 32    | `00 00 00 4B` | 75            | Frequency Min |
| Tag 9A            | +116   | 1      | 8     | `9A`          | 154           | - |
| **Unknown**       | +117   | 4      | 32    | `00 00 00 5F` | 95            | Frequency Max|
| Tag 9B            | +121   | 1      | 8     | `9B`          | 155           | - |
| **Unknown**       | +122   | 4      | 32    | `00 00 00 0C` | 12            | Unknown |
| Tag 9C            | +126   | 1      | 8     | `9C`          | 156           | - |
| **Unknown**       | +127   | 4      | 32    | `A1 B2 C3 D4` | 2712847316    | Unknown |
| Tag 9D            | +131   | 1      | 8     | `9D`          | 157           | - |
| **Unknown**       | +132   | 4      | 32    | `A1 B2 C3 D4` | 2712847316    | Unknown |
| Tag 9E            | +136   | 1      | 8     | `9E`          | 158           | - |
| **Unknown**       | +137   | 4      | 32    | `A1 B2 C3 D4` | 2712847316    | Unknown |
| Tag 9F            | +141   | 1      | 8     | `9F`          | 159           | - |
| **Unknown**       | +142   | 4      | 32    | `A1 B2 C3 D4` | 2712847316    | Unknown |
| Tag A0            | +146   | 1      | 8     | `A0`          | 160           | - |
| **Bytes in Ping** | +147   | 4      | 32    | *Varies*      | *Varies*      | Number of bytes in ping returns |
| End Header        | +151   | 1      | 8     | `21`          | 33            | End of ping header | -->

<!-- Example of first and last 4 sonar records from sonar files.  Values displayed are in hexadecimal.

**1199**
![Img of 1199 Son Header](./attach/1199SonHead.PNG)

**Helix**
![Img of Helix Son Header](./attach/HelixSonHead.PNG) -->
