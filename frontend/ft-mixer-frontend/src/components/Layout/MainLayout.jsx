import React from 'react';
import ImageViewerContainer from '../ImageViewer/ImageViewerContainer';
import ImagePairViewer from '../ImageViewer/ImagePairViewer';
import Sidebar from './Sidebar';

const MainLayout = () => {
  return (
    <div className="flex h-screen w-screen bg-background p-1 gap-1">
      {/* Left Container: Inputs (2x2 Grid - 4 images) */}
      <div className="flex-1 grid grid-cols-2 grid-rows-2 gap-1 h-full">
        <ImagePairViewer id={0} title="IMG_01" />
        <ImagePairViewer id={1} title="IMG_02" />
        <ImagePairViewer id={2} title="IMG_03" />
        <ImagePairViewer id={3} title="IMG_04" />
      </div>

      {/* Right Container: Sidebar + Outputs */}
      <div className="w-[600px] flex flex-row gap-1 h-full">
        {/* Top Right: Sidebar Controls */}
        <div className="h-full w-[300px]">
            <Sidebar />
        </div>

        {/* Bottom Right: Outputs (1x2 Grid) */}
        <div className="h-full grid grid-rows-2 gap-1 flex-1">
            <ImageViewerContainer id={0} type="output" title="Output 1" />
            <ImageViewerContainer id={1} type="output" title="Output 2" />
        </div>
      </div>
    </div>
  );
};

export default MainLayout;