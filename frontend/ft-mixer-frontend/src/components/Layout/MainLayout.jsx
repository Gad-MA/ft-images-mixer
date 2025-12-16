import React from 'react';
import ImageViewerContainer from '../ImageViewer/ImageViewerContainer';
import Sidebar from './Sidebar';

const MainLayout = () => {
  return (
    <div className="flex h-screen w-screen bg-background p-2 gap-2">
      {/* Left Container: Inputs (2x2 Grid) */}
      <div className="flex-1 grid grid-cols-2 grid-rows-2 gap-2 h-full">
        <ImageViewerContainer id={0} type="input" title="Image 1" />
        <ImageViewerContainer id={1} type="input" title="Image 2" />
        <ImageViewerContainer id={2} type="input" title="Image 3" />
        <ImageViewerContainer id={3} type="input" title="Image 4" />
      </div>

      {/* Right Container: Sidebar + Outputs */}
      <div className="w-[450px] flex flex-col gap-2 h-full">
        {/* Top Right: Sidebar Controls */}
        <div className="h-1/2">
            <Sidebar />
        </div>

        {/* Bottom Right: Outputs (1x2 Grid) */}
        <div className="h-1/2 grid grid-rows-2 gap-2">
            <ImageViewerContainer id={0} type="output" title="Output 1" />
            <ImageViewerContainer id={1} type="output" title="Output 2" />
        </div>
      </div>
    </div>
  );
};

export default MainLayout;