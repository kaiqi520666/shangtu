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

export function hasUploadingImages(uploadedImages) {
  return (uploadedImages || []).some((img) => img?.uploading);
}
