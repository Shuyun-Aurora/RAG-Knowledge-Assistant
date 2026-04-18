import React from 'react';
import { Carousel, Typography } from 'antd';
import "../css/banner.css"

const { Title, Text } = Typography;

const BannerCarousel = ({ banners }) => (
  <div className="banner-carousel">
    <Carousel autoplay effect="fade">
      {banners.map((item, idx) => (
        <div key={idx}>
          <div className="banner-slide">
            <img src={item.img} alt={item.title} className="banner-img" />
            <div className="banner-mask" />
            <div className="banner-content">
              <Title level={2} style={{ color: 'white', marginBottom: 8 }}>{item.title}</Title>
              <Text style={{ fontSize: 20, color: 'white' }}>{item.desc}</Text>
            </div>
          </div>
        </div>
      ))}
    </Carousel>
  </div>
);

export default BannerCarousel; 