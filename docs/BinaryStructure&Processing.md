
# Humminbird Recording: Binary Structure & Processing
By Cameron S. Bodine

## Introduction
PyHum (citation) is an open-source python framework for reading and processing from a low-cost Humminbird sidescan sonar system.  Originally developed for Python 2, it can read in Humminbird DAT and SON files, export the data, process radiometric corrections, classify bed texture, and produce maps.  Since its release, additional and enhanced functionality has been identified by the software authors and end-users, including Python 3 compatibility.  This report documents new workflows for decoding Humminbird binary sonar recordings that will work on sonar recordings from any Humminbird model with any firmware version.  The goal and objectives for this effort are as follows:

- Ensure functionality with all current Humminbird models.
    - Collect and catalog sonar recordings from various Humminibrd models (in progress)
    - Develop workflows to test PyHum on sonar recording catalog. (in progress)
    - Identify and implement alternative workflows for decoding binary sonar recordings. (in progress)

This report documents a new workflow for decoding and loading sonar recordings, and exporting non-rectified imagery.  First, new findings concerning the DAT and SON binary file structure will be discussed.  Next, two new Python scripts for processing these files will be discussed.  Finally, these new workflows will be tested against a variety of Humminbird sonar recordings to determine if they can successfully decode the binary structure and export relevant data.

## DAT and SON Binary Structure
The initial release of PyHum documented the known binary structure of Humminbird sonar files (https://github.com/dbuscombe-usgs/PyHum/blob/master/docs/data_formats.rst).  Using this as a guide, DAT and SON files were further explored using a program called Hexinator (https://hexinator.com/).  Hexinator interface allows you to quickly view binary data in hexidecimal format.  It has a tool that allows you to annotate the file with known structures and elements, known as a grammer, which can be applied to any open binary file which aides in seeing differences in the binary structure.

![Img of Hexinator Program](/docs/attach/Hexinator.PNG?raw=true "Hexinator Screen Shot")

### SON File Structure
A SON file contains every sonar ping for a specific sonar channel.  File names correspond to the following sonar channels:

| File Name | Description                 | Frequency         |
| --------- | --------------------------- | ----------------- |
| B000.SON  | Low Frequency Down Scan     | 50/83 kHz         |
| B001.SON  | High Frequency Down Scan    | 200 kHz           |
| B002.SON  | Side Scan Port              | 455/800/1,200 kHz |
| B003.SON  | Side Scan Starboard         | 455/800/1,200 kHz |
| B004.SON  | Mega Frequency Down Scan    | 1,200 kHz         |

Each SON file contains all the pings (sonar return) that were recorded.  Each ping begins with a header, containing metadata specific to that ping (see additional information below).  The header is followed by 8-byte (0-255 Integer) values representing all the returns for that ping.  The header and sonar returns will be collectively referred to as a sonar record.  All data stored in SON files are signed integer big endian.

#### Sonar Record Structure
The number of bytes for a sonar record varies in two ways.  First, depending on the model (and potentially firmware version), the number of bytes in the sonar record header vary in length.  Three different lengths have been identified so far:

| Header Length | Humminbird Model |
| ------------- | ---------------- |
| 67 Bytes      | 9xx              |
| 72 Bytes      | 11xx, Helix, Onix|
| 152 Bytes     | Solix            |

Second, the number of sonar returns for a sonar record vary depending on the range setting on the unit.  The variability in the size of a sonar record across recordings and Humminbird model make automatically decoding the file a non-trivial task.  Each sonar record always begins with the same four hexidecimal values: `C0 DE AB 21`.  This sequence is common to all sonar recordings encountered to date.  The header then terminates with the following hexidecimal sequence: `A0 ** ** ** ** 21` where the `** ** ** **` is a 32-byte unsigned integer indicating the number of sonar returns that are recorded immediately after `21`.  By simply counting the number of bytes beginning at `C0` and terminating at `21`, the correct header length can be determined.

##### Header Structure
The header for a sonar record contains metadata specific to that sonar record.  Information about the ping location, time elapsed since beginning of the recording, heading, speed, depth, etc. are contained in this structure.  This data is always preceded by a hexidecimal value that is unique for the data that follows, referred to as a tag.  For example, `Depth` is always tagged by a hexidecimal value of `87`.  While the variety of information that is stored in the header varies by Humminbird model, tags consistently identify the type of information that follows.  The following sections indicate the tags, offset, the data that follows the tag, and the size (in bytes) of the data.

##### Humminbird 900 Series
Header Length (Bytes): **67**

| Name              | Offset | Length | Bytes | Hex Value     | Integer Value | Description |
| ----------------- | ------ | ------ | ----- | ------------- | ------------- | ----------- |
| Head Start        | +0     | 4      | 32    | `A0 DE AB 21` | 3235818273    | Beginning of Sonar Record |
| Tag 80            | +4     | 1      | 8     | `80`          | 128           | - |
| **Record Number** | +5     | 4      | 32    | *Varies*      | *Varies*      | Unique sonar record id |
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
| **Sonar Beam**    | +40    | 1      | 8     | *Varies*      | *Varies*      | 0=low freq down; 1=hi freq down; 2=SI Port; 3=SI Star; 4=very high down |
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
| Bytes in Ping     | +62    | 4      | 32    | *Varies*      | *Varies*      | Number of bytes in ping returns |
| End Head          | +66    | 1      | 8     | `21`          | 33            | End of sonar record header |


##### Humminbird 1100 & Helix Series
Header Length (Bytes): **72**  
*Note:* The structure is the same as 900 series for offset 0 - 33.

| Name              | Offset | Length | Bytes | Hex Value     | Integer Value | Description |
| ----------------- | ------ | ------ | ----- | ------------- | ------------- | ----------- |
| Head Start        | +0     | 4      | 32    | `A0 DE AB 21` | 3235818273    | Beginning of Sonar Record |
| Tag 80            | +4     | 1      | 8     | `80`          | 128           | - |
| **Record Number** | +5     | 4      | 32    | *Varies*      | *Varies*      | Unique sonar record id |
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
| **Sonar Beam**    | +45    | 1      | 8     | *Varies*      | *Varies*      | 0=low freq down; 1=hi freq down; 2=SI Port; 3=SI Star; 4=very high down |
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
| Bytes in Ping     | +67    | 4      | 32    | *Varies*      | *Varies*      | Number of bytes in ping returns |
| End Head          | +71    | 1      | 8     | `21`          | 33            | End of sonar record header |


##### Humminbird Solix Series
Header Length (Bytes): **152**  
*Note:* The structure is the same as 1100/Helix series for offset 0 - 43.

| Name              | Offset | Length | Bytes | Hex Value     | Integer Value | Description |
| ----------------- | ------ | ------ | ----- | ------------- | ------------- | ----------- |
| Head Start        | +0     | 4      | 32    | `A0 DE AB 21` | 3235818273    | Beginning of Sonar Record |
| Tag 80            | +4     | 1      | 8     | `80`          | 128           | - |
| **Record Number** | +5     | 4      | 32    | *Varies*      | *Varies*      | Unique sonar record id |
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
| **Sonar Beam**    | +85    | 1      | 8     | *Varies*      | *Varies*      | 0=low freq down; 1=hi freq down; 2=SI Port; 3=SI Star; 4=very high down |
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
| **Unknown**       | +112   | 4      | 32    | `00 00 00 4B` | 75            | Unknown |
| Tag 9A            | +116   | 1      | 8     | `9A`          | 154           | - |
| **Unknown**       | +117   | 4      | 32    | `00 00 00 5F` | 95            | Unknown |
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
| Bytes in Ping     | +147   | 4      | 32    | *Varies*      | *Varies*      | Number of bytes in ping returns |
| End Head          | +151   | 1      | 8     | `21`          | 33            | End of sonar record header |


Example of first and last 4 sonar records from randomly selected sonar files:

**1199**
![Img of 1199 Son Header](/docs/attach/1199SonHead.PNG?raw=true "Hexinator Screen Shot")

**Helix**
![Img of Helix Son Header](/docs/attach/HelixSonHead.PNG?raw=true "Hexinator Screen Shot")
