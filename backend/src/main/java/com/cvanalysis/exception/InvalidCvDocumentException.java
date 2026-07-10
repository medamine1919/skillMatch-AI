package com.cvanalysis.exception;

public class InvalidCvDocumentException extends RuntimeException {
    public InvalidCvDocumentException(String message) {
        super(message);
    }
}