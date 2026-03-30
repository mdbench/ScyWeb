# ScyWeb
ScyWeb is a lightweight, deployable web application that lets users scramble and unscramble image files from a browser.

## Why is it called ScyWeb?
A scytale is an ancient Greek transposition cipher that utilizes a rod and parchment to scramble and unscramble messages. ScyWeb was developed to provide an image cipher experience using web technologies.

## Why do we need it?
Browsers have become state of the art applications. Many apps available on app stores can be made with wider compatibility for fractions of the code-base and energy. ScyWeb is only 345 lines of code at its base. Cybersecurity is getting harder and harder to achieve and an offline web app makes hacking virtually impossible, a breath of fresh air in a time of insecurity.

## Image scrambling
Lossless compression is not used on unscrambled images so the original image might be much smaller when compared to the new unscrambled image. Preliminary checks have identified scrambled images without lossless compression substantially smaller than images encrypted to plain text. A scrambled image is a much better option than encrypting images and a more secure option than encrypting an entire database or container of images and decrypting that database or container on application boot up. Image scrambling can be used in conjunction with current compression algorithms without causing issues. Unfortunately, the default mode does not show a proof of concept for a smaller scrambled file size when compared to an encrypted string but the alternative mode (under development) does. The important alternative method metrics have been listed below:

![Image Scrambling Metrics - Scrambling versus Encryption](https://raw.githubusercontent.com/mdbench/ScyWeb/master/Screenshot-2026-03-29-7.57.16-PM.png)

An encrypted string of the original image [glacier_og_image_4503x3002.jpg](https://raw.githubusercontent.com/mdbench/ScyWeb/refs/heads/main/glacier_og_image_4503x3002.jpg) is 2.3MBs. You can see the methodology used to convert images to encrypted strings by visiting [the image to string converter demo](https://demos.matthewbenchimol.com/ScyWeb/ScyWebConverter.html). Without lossless compression, a scrambled version of the original image is 12.9MBs. With lossless compression, a scrambled version of the original image is 1.3MBs. This was surprising, as it indicated a scrambled image file size could actually be lower than the original copy. The alternative method uses block-chunking using similar nearest neighbors enhancing compression algorithims.

### Full compression test conducted. Results of tests below:
- [glacier_og_image_4503x3002.jpg fully compressed = 904KBs](https://raw.githubusercontent.com/mdbench/ScyWeb/refs/heads/main/FINAL_SIZE_MAX_COMPRESSION_glacier_og_image_4503x3002.jpg)
- [enc_glacier_og_image_4503x3002_scrambled.jpg fully compressed = 1.11MBs](https://raw.githubusercontent.com/mdbench/ScyWeb/refs/heads/main/FINAL_SIZE_MAX_COMPRESSION_ALTERNATIVE_METHOD_enc_glacier_og_image_4503x3002_scrambled.jpg)

> Encrypted string is 100%+ larger than scrambled image. Difference between fully compressed original image and fully compressed scrambled image is 20%+ larger file size. Viability of scrambling images as a substitute for image to string encryption confirmed.

### Quantum-resistant method
Still under development but color diffusion is present in a unique format and looks to impossible to unscramble using heuristic algorithms.

> Encrypted string is 15%+ larger than scrambled image. Unfortunately, quantum resistant method is not compatible with compression, as it has too many pixel re-replication errors.

#### Success of image scrambling for tailored use cases is high. Unique viable use for making uninterrupted and uncompromised streaming, making a video stream unable to be modified in transit when delivered to users in real-time, offloading costs to user devices when it comes to unscrambling and re-rendering. Other uses include secure Bluerays, DVDs, and new age optical drives. Advanced use cases for movies delivered to theaters to prevent bootlegging. More use cases being tested but the sky is the limit.

## Movie scrambling
Lossless compression is not used on unscrambled movies so the original movie might be much smaller when compared to the new unscrambled movie. Scrambled movies are much bigger in their scrambled form than movies that use pixel information sharing, as this gets lost in the enciphering process. This is an area for further development. It means encrypted movies are smaller in size than scrambled movies. Below is a demo showing image scrambling being used on Big Buck Bunny at 1080 and then being converted back to unscrambled. There is no visual difference between the movies before and after scrambling and unscrambling them.
- [Demo](https://demos.matthewbenchimol.com/ScyWeb/ScyWebVideoTester.html)
- [Original Big Buck Bunny](https://raw.githubusercontent.com/mdbench/ScyWeb/refs/heads/main/Big_Buck_Bunny_1080_10s_30MB.mp4)
- [Unscrambled Big Buck Bunny](https://raw.githubusercontent.com/mdbench/ScyWeb/refs/heads/main/enc_BBB_Unscrambled.mp4)

## Due-Outs
- Fix pixel re-replication issue on alternative method
- Add bulk image download as .zip option
- Integrate image scrambling into HelioWeb

## Want to contribute?
Send me a pull request.

