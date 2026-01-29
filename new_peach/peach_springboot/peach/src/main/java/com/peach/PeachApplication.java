package com.peach;

import org.mybatis.spring.annotation.MapperScan;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;

@SpringBootApplication
@MapperScan("com.peach.mapper")
public class PeachApplication {

    public static void main(String[] args) {
        SpringApplication.run(PeachApplication.class, args);
    }

}
