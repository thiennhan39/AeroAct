# Raw Data Quality Audit

- total annotation episodes: `10113`
- done episodes: `9942`
- bad/skipped episodes: `171`
- partial bad episodes: `3`
- frame count min/max/mean: `1` / `368` / `102.48`
- done episodes <5 frames: `77`
- done episodes <10 frames: `192`
- done episodes <20 frames: `485`
- quality flagged episodes: `195`

## Bad Episodes By Scene

```json
{
  "2": 46,
  "3": 2,
  "5": 1,
  "8": 26,
  "10": 17,
  "12": 26,
  "14": 24,
  "17": 23,
  "20": 6
}
```

## Quality Flag Counts

```json
{
  "short_lt10": 115,
  "very_dark_sample": 3,
  "very_short_lt5": 77
}
```

## Shortest Done Episodes

- scene `17` episode `3LOTDFNYAGX43VZV91W35UKU3XQFWQ` frames `1`
- scene `17` episode `3WYGZ5XF35DMC0A0Q7DZOI9E46IKS4` frames `1`
- scene `17` episode `34J10VATJOWJTP5ZY03IG2F0UJOQI0` frames `1`
- scene `10` episode `3X1FV8S5J6PX26VLUBXP1D1SPMYGVK` frames `1`
- scene `17` episode `3MRNMEIQWE4RUH90EHUB8J0TTDMDL0` frames `1`
- scene `17` episode `3T111IHZ5NOQUPRW7LM58ZQ27AI9R6` frames `1`
- scene `10` episode `3UOUJI6MTMC8BD1BEVNOTDZ4EBJXUE` frames `1`
- scene `17` episode `3R2UR8A0IJEDY8HEI9BFU77F3QOXO3` frames `1`
- scene `10` episode `3YWRV122C1XIWC036NBWDEIBN28U81` frames `1`
- scene `14` episode `3PJUZCGDJFEKCKC08CG5HIVXHIT89S` frames `2`
- scene `14` episode `3E47SOBEYZUFZOVGTI2NWXQJQ3YCIQ` frames `2`
- scene `14` episode `3NAPMVF0Z5D5CMMIDY9KTVROXYD72L` frames `2`
- scene `14` episode `3AQF3RZ55HG69GKPIJJZ70LHEKJF6O` frames `2`
- scene `8` episode `3S06PH7KS02E4A5WL7CSO4RFMFT1D1` frames `3`
- scene `8` episode `358010RM5NR8OSQBJLXTPZ1NR2SVX4` frames `3`
- scene `8` episode `35K3O9HUAKBAMVD4O12XJODUN21EFY` frames `3`
- scene `8` episode `3TMFV4NEPHCVOGP81NQXV23872ZW8L` frames `3`
- scene `8` episode `337RC3OW0E0DOY9M52U5E560KRYLVK` frames `3`
- scene `8` episode `3C6FJU71TZRXBIRLJR9QCR6DF1CUYJ` frames `3`
- scene `8` episode `39N5ACM9HNL5ICBHUTIG34QNY9L9PV` frames `3`
- scene `8` episode `3D4CH1LGEJRZ5ZIIRAST9VCVXJQ9GL` frames `3`
- scene `8` episode `3AAJC4I4FPQO2SQW3E7VJW644DTZJQ` frames `3`
- scene `8` episode `3L6L49WXW9V0SWNMTJDBOQAQLJ1548` frames `3`
- scene `8` episode `3W92K5RLW3FZM961DFEYXGA380Q5VG` frames `3`
- scene `8` episode `3LOTDFNYAGX43VZV91W35UKUUAHFWY` frames `3`
- scene `8` episode `3KRVW3HTZWJH2OA3BJQF3V1ILVVMSP` frames `3`
- scene `8` episode `3VA45EW49WL587WLBGQ8ZY3EQTSO1D` frames `3`
- scene `8` episode `3TPZPLC3M9AJ3AM1DKH6CRN1YJ73P8` frames `3`
- scene `10` episode `36PW28KO48UFQ4WWDLG55N23PTPEAZ` frames `3`
- scene `8` episode `3R0T90IZ11A13XPL3U2KBLD335SGCA` frames `3`

## Files

- bad list: `/workspace/AeroAct_ws/AeroAct/Dataset/AerialVLN-Dataset/Raw_data/aerialvln-s/bad_episodes.json`
- training exclusion list: `/workspace/AeroAct_ws/AeroAct/Dataset/AerialVLN-Dataset/Raw_data/aerialvln-s/excluded_for_training.json`
- full audit JSON: `/workspace/AeroAct_ws/AeroAct/Dataset/AerialVLN-Dataset/Raw_data/aerialvln-s/raw_data_quality_audit.json`