export function buildProductAnalyzeImages(uploadedImages, mainImageIndex = 0) {
  const indexedImages = (uploadedImages || [])
    .map((img, index) => ({ img, index }))
    .filter(({ img }) => img?.url);

  if (indexedImages.length === 0) {
    return [];
  }

  const primaryIndex = indexedImages.some(({ index }) => index === mainImageIndex)
    ? mainImageIndex
    : indexedImages[0].index;
  let detailNumber = 1;

  return indexedImages.map(({ img, index }) => {
    if (index === primaryIndex) {
      return { url: img.url, label: "主图" };
    }
    const label = `细节图${detailNumber}`;
    detailNumber += 1;
    return { url: img.url, label };
  });
}

export function buildVideoAnalyzeImages(inputMode, uploadedImages) {
  const images = (uploadedImages || []).filter((img) => img?.url);

  if (inputMode === "image_to_video") {
    return images.slice(0, 1).map((img) => ({ url: img.url, label: "首帧图" }));
  }

  return images.slice(0, 9).map((img, index) => ({
    url: img.url,
    label: `参考图${index + 1}`,
  }));
}

export function buildOutfitAnalyzeImages(garmentImages, mainGarmentIndex = 0, selectedModel = null) {
  const images = buildProductAnalyzeImages(garmentImages, mainGarmentIndex).map((item) => ({
    ...item,
    label: item.label === "主图" ? "服装主图" : item.label.replace("细节图", "服装细节图"),
  }));

  if (selectedModel?.image) {
    images.push({
      url: selectedModel.image,
      label: "模特参考图",
    });
  }

  return images;
}

export function hasUploadingImages(uploadedImages) {
  return (uploadedImages || []).some((img) => img?.uploading);
}
